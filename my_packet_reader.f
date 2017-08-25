c **********************************************************************
c *                                                                    *
c *     module: pvars                                                  *
c *                                                                    *
c *     contains global variables                                      *
c *                                                                    *
c *     Use saved_dp1, saved_dp2, saved_dp3, saved_step, saved_int1,   *
c *     saved_int2, and saved_int3, when data from one packet          *
c *     subroutine is needed in following packet subroutines.          *
c *     If more than 3 double precision or integer variables are       *
c *     needed, add additional variables to this module.               *
c *                                                                    *
c **********************************************************************
c
c
      module pvars
      implicit none
c
c
c
      double precision saved_dp1, saved_dp2, saved_dp3
      integer packet_file_no /1/, screen /6/, key /5/,
     &        results_file_no /2/, saved_step, saved_int1,
     &                             saved_int2, saved_int3
      character * 80 packet_file_name, results_file_name
      logical ou_packet_control(30), debug
c
c
c
c
      end module pvars
c
c
c
c **********************************************************************
c *                                                                    *
c *     program: packet_reader                                         *
c *                                                                    *
c *     Main program controlling packet reading.  Calls appropriate    *
c *     subroutines to operate on packets when needed, or skips over   *
c *     unwanted packets.                                              *
c *                                                                    *
c **********************************************************************
c
c
c
      program packet_reader
      use pvars
      implicit none
c
      integer ios,type,num_lines,step,iter,lines_read,counter
c
c
      counter = 0
c
c
c                   call subroutines to initialize variables,
c                   open packet file, and obtain the desired
c                   packet types from the user.
c
c
      call init
      call get_packet_type
c
c
c                   infinite loop, reading packets until the end of
c                   file is reached.
c
c
      debug = .false.
      do
c
c                   read packet header line.
c
c
         read(unit=packet_file_no,iostat=ios)type,num_lines,step,iter
c
c
c                   check for errors in reading the packet file,
c                   or for the end of file, terminate program when
c                   appropriate.
c
c
         if( debug ) write(screen,*)type,num_lines,step,iter,ios
c
         if( ios .gt. 0)then
            call closer(packet_file_no)
            call closer(results_file_no)
            write(screen,9000)
            stop
         else if( ios .lt. 0 ) then  ! -1 means eof on prior read
            if( counter .eq. 0 ) write(screen,9200)
            call closer(packet_file_no)
            call closer(results_file_no)
            write(screen,9100)
            stop
         end if
c
c                   check to see if the current packet type should
c                   be analyzed.  ou_packet_control(type) will be set
c                   to true when the user specifies that type to be
c                   processed.
c
         if( ou_packet_control ( type ) ) then
c
c
c                   keep track of the number of times the desired
c                   packets are found, message will be sent if
c                   no desired packets are found on the packet file.
c
c
            counter = counter + 1
c
c                   case(#) need to be added as packets are added
c
c
            select case(type)
c
               case(31)
                  call cohesive_tractions_packet(type,num_lines,
     &                         step,iter)
c
               case(32)
                  call cohesive_disp_jumps_packet(type,
     &                   num_lines,step,iter)
            end select
c
         else
c
c
c                   skip unwanted packets.
c
c
            do lines_read=1,num_lines
               read(unit=packet_file_no,iostat=ios)
     &                           type,num_lines,step,iter
               if( ios .gt. 0)then
                  call closer(packet_file_no)
                  call closer(results_file_no)
                  write(screen,9000)
                  stop
               else if( ios .lt. 0 )then
                  if( counter .eq. 0 ) write(screen,9200)
                  call closer(packet_file_no)
                  call closer(results_file_no)
                  write(screen,9100)
                  stop
               end if
            end do
c
         end if
c
      end do
c
c
      call closer(packet_file_no)
      call closer(results_file_no)
      stop
c
 9000 format(/,1x,'>> ERROR: reading packet file...terminating m',/)
 9100 format(/,1x,'>> END OF FILE...program terminating in main',/)
 9200 format(/,1x,'>> ERROR: the desired packet type can not be',
     &       /,1x,'          found in the given packet file.')
c
c
      end
c
c
c
c **********************************************************************
c *                                                                    *
c *     subroutine: init                                               *
c *                                                                    *
c *     initializes variables, gets packet file name from user, and    *
c *     opens the file.                                                *
c *                                                                    *
c **********************************************************************
c
c
      subroutine init
      use pvars, only: screen,key,packet_file_no,
     &        packet_file_name,ou_packet_control,debug
      implicit none
      integer ios
c
c
c                   ou_packet_control is an array of logical
c                   variables, which are set to true when the
c                   user specifies that a type of packet should
c                   be analyzed.  all components of the array
c                   are set to false initially.
c
      ou_packet_control = .false.
c
      debug = .false.
c
c
      write(screen,9000)
c
c
c                   loop until a valid packet file is given
c                   and opened.
c
c
      do
        write(screen,9010)
        read(key,9020) packet_file_name
        call stripf( packet_file_name )
        if ( packet_file_name(1:1) .eq. ' ' ) then
            packet_file_name(1:) = 'packet.out.1'
        end if
        open( unit=packet_file_no, file=packet_file_name, status='old',
     &        access='sequential', form='unformatted',
     &        position='rewind', iostat=ios)
        if( ios .ne. 0)then
           write(screen,9030)
        else
           write(screen,9040)
           exit
        end if
      end do
c
      return
c
c
 9000 format(/,
     &       ' ****************************************************',
     &  /,   ' *                                                  *',
     &  /,   ' *   WARP3D Packet Reader (MODIFIED BY VSP)         *',
     &  /,   ' *                                                  *',
     &  /,   ' *             Last updated: 08-25-2017             *',
     &  /,   ' *                                                  *',
     &  /,   ' *                                                  *',
     &  /,   ' ****************************************************'
     &   )
 9010 format(/,1x, '>> WARP3D binary packet file',/,
     &               ' >>   (default: packet.out.1) ? ',$)
 9020 format(a80)
 9030 format(/,1x, '>> ERROR: Invalid packet file')
 9040 format(/,1x, '>> Packet file opened',/)
c
      end
c
c **********************************************************************
c *                                                                    *
c *     subroutine: closer                                             *
c *                                                                    *
c *     closes both the packet file and the output file.               *
c *                                                                    *
c **********************************************************************
c
      subroutine closer(file)
      use pvars, only: screen
      implicit none
      integer, intent(in):: file
c
      logical connected
c
c
      inquire( unit=file, opened=connected)
      if( connected )then
        close(unit=file, status='keep')
        if(file .eq. 1)write(screen,1000)
        if(file .eq. 2)write(screen,2000)
      end if
      return
 1000 format(/,1x,'>> Packets file closed')
 2000 format(/,1x,'>> Results file closed')
      end
c
c *****************************************************************
c *                                                               *
c *      s u b r o u t i n e  -- s t r i p f                      *
c *                                                               *
c *****************************************************************
c
      subroutine stripf( string )
      implicit integer (a-z)
      character *(*) string, copy*256
c
c             strip leading blanks from string and return it.
c
      last = len(string)
      copy(1:last) = string(1:last)
      do 100 cpos = 1, last
       if ( string(cpos:cpos) .ne. ' ' ) go to 200
 100  continue
      return
 200  continue
      string(1:) = copy(cpos:last)
      return
      end
c
c **********************************************************************
c *                                                                    *
c *     subroutine: get_packet_type                                    *
c *                                                                    *
c *     collects all of the desired packet types from the user.        *
c *                                                                    *
c **********************************************************************
c
      subroutine get_packet_type
c
      use pvars, only: screen,key,packet_file_no,
     &                 ou_packet_control     
      implicit none
c
      character(len=1) :: y_or_n
      integer :: output_packet_no
      logical :: additional_packets_needed, valid_packet_no
c
c
      additional_packets_needed = .true.
      valid_packet_no = .true.
c
c
c                   loop asks user what type of packet is
c                   desired, repeats until all deired packets
c                   have been recorded.
c
c
      do
         write(screen,9000)
         valid_packet_no=.true.
         do
           read(key,9100)output_packet_no
           if(output_packet_no .gt. 32 .or.
     &        output_packet_no .lt. 0)then
                write(screen,9200)
                write(screen,9300)
           else
                call is_packet_implemented(output_packet_no,
     &                                valid_packet_no)
                if(valid_packet_no)then
                   write(screen,9300)
                else
                   exit
                end if
           end if
         end do
c
         ou_packet_control(output_packet_no)=.true.
c
c        remove ability to request multiple packets,
c        because this will mess up the python reader.
c        just exit loop.
        exit
c
C          write(screen,9400)
C          read(key,9500)y_or_n
C          if(y_or_n .eq. 'N' .or.
C      &      y_or_n .eq. 'n' .or.
C      &      y_or_n .eq. ' ')exit
c
      end do
c
      return
c
 9000 format(/,1x,'        Packet Types/Numbers              ',/,
     &         1x,'                                          ',/,
     &         1x,'          Type                    Number  ',/,
     &         1x,'   -------------------            ------  ',/,
     &         1x,'   deleted (not implemented)      1 - 30  ',/,
     &         1x,'   interface tractions of element   31    ',/,
     &         1x,'   interface displ jumps of element 32    ',/,
     &       /,1x,'>> see Dodds packet_reader.f for other packets.',
     &       /,1x,'>> Enter desired packet number: ',$)
 9100 format(i3)
 9200 format(/,1x,'>> ERROR: Invalid packet number',
     &       /,1x,'>>        Pick a valid packet number')
 9300 format(/,1x,'>> Enter desired packet number: ',$)
 9400 format(/,1x,'>> Are additional packets desired?',
     &            ' (y or n) (n is the default): ',$)
 9500 format(a1)
      end
c
c
c
c **********************************************************************
c *                                                                    *
c *     subroutine: is_packet_implemented                                   *
c *                                                                    *
c *     checks to see if the desired packet has been added to this     *
c *     program.  as packet types are added, the packet number is      *
c *     removed from this list.                                        *
c *                                                                    *
c **********************************************************************
c
c
c
c
      subroutine is_packet_implemented(number,control)
      use pvars, only: screen
      implicit none
c
      integer, intent(in)::number
      logical, intent(inout)::control
c
c
c
c             must update when a new packet is added
c
c
      select case ( number )
c
        case ( 31, 32 )
          control = .false.
c       
        case default
          write(screen,1000) number
c       
      end select
c
      return
c
c
c
 1000 format(/,1x,'>> ERROR: Packet number ',i2,
     &          ' has not been implimented yet. Pick again')
c
      end
c
c
c
c **********************************************************************
c *                                                                    *
c *     subroutine: open_output_file                                   *
c *                                                                    *
c *     this subroutine is called from a specific packet types         *
c *     subroutine. it will open the output file where the results     *
c *     should be written.                                             *
c *                                                                    *
c **********************************************************************
c
c
      subroutine open_output_file
      use pvars, only: screen, results_file_name, results_file_no, key
      implicit none
c
      integer ios
c
      do
        write(screen,9010)
        read(key,9020) results_file_name
        call stripf( results_file_name )
        if ( results_file_name(1:1) .eq. ' ' ) then
            results_file_name(1:) = 'results.out.1'
        end if
        open( unit=results_file_no, file=results_file_name,
     &        status='replace',iostat=ios)
        if( ios .ne. 0)then
           write(screen,9030)
        else
           write(screen,9040)
           exit
        end if
      end do
c
      return
c
c
c
 9010 format(/,1x, '>> Name of results file',/,
     &               ' >>   (default: results.out.1)? ',$)
 9020 format(a80)
 9030 format(/,1x, '>> ERROR: opening results file')
 9040 format(/,1x, '>> Results file opened'  )
c
      end
c
c
c **********************************************************************
c *                                                                    *
c *     subroutine: cohesive_tractions_packet                          *
c *                                                                    *
c *     reads packet file for tractions of interface-cohesive          *
c *     elements
c *                                                                    *
c *     THIS SUBROUTINE SHOULD BE MODIFIED BY THE USER TO OUTPUT       *
c *     THE DESIRED DATA TO THE RESULTS FILE.                          *
c *                                                                    *
c **********************************************************************
c
c
      subroutine cohesive_tractions_packet( type,
     &     num_lines, step, iter)
      use pvars, only: screen, key, packet_file_no, results_file_no
      implicit none
c
      integer, intent(in):: type, num_lines, step, iter
c
c                  local declarations
c
      integer nvalues, lines_read, ios, elem, point, cohesive_type
      double precision values(20)
      logical connected
c
      inquire( unit=results_file_no, opened=connected )
      if( .not. connected ) call open_output_file
c
c                  read and write to output file
c
c                  effective reading of tractions must be
c                  aware of the cohesive model type to
c                  know number & type of data values
c
c                  set type below. may wish to alter based on
c                  element number.
c
c                  cohesive types:
c                    1 = linear-elastic   2,3,5 not used
c                    4 = exponential model 6 = ppr
c                    7 = creep
c
c
      cohesive_type = 8
c
      if( cohesive_type == 1 ) nvalues = 6
      if( cohesive_type == 4 ) nvalues = 8
      if( cohesive_type == 6 ) nvalues = 8
      if( cohesive_type == 7 ) nvalues = 0
      if( cohesive_type == 8 ) nvalues = 6

      write(results_file_no,1100) cohesive_type, nvalues
      write(results_file_no,1200)
c
      do lines_read = 1, num_lines
       read(packet_file_no,iostat=ios) elem, point, values(1:nvalues)
       if( ios .gt. 0 ) then
         call closer(packet_file_no)
         call closer(results_file_no)
         write(screen,9000)
         stop
       else if( ios .lt. 0 )then
         call closer(packet_file_no)
         call closer(results_file_no)
         write(screen,9100)
         stop
       end if
       write(results_file_no,1000) step, elem, point,
     &                             values(1:nvalues)
      end do
c
      return
c
 1000 format(1x,i5,',',i8,',',i6,',', 
     &                     e14.6,',',e14.6,',',e14.6,',',e14.6,',',
     &                     e14.6,',',e14.6,',',e14.6,',',e14.6)
 1100 format(/,1x,'# Interface-cohesive tractions packet (type=31)....',
     & /,1x,'# cohesive model type: ',i2,2x,'nvalues: ',i2 )
 1200 format(' #   step element  point',10x,20('-'),' values ',20('-'))
 9000 format(/,1x,'>> ERROR: reading packet file..terminating in '
     &                      'cohesive_tractions_packet subroutine')
 9100 format(/,1x,'>> END OF FILE...program terminating in disp')
c
      end
c
c
c **********************************************************************
c *                                                                    *
c *     subroutine: cohesive_disp_jumps_packet                         *
c *                                                                    *
c *     reads packet file for displacement jumps of interface-cohesive *
c *     elements                                                       *
c *                                                                    *
c *     THIS SUBROUTINE SHOULD BE MODIFIED BY THE USER TO OUTPUT       *
c *     THE DESIRED DATA TO THE RESULTS FILE.                          *
c *                                                                    *
c **********************************************************************
c
c
      subroutine cohesive_disp_jumps_packet( type,
     &     num_lines, step, iter)
      use pvars, only: screen, key, packet_file_no, results_file_no
      implicit none
c
      integer, intent(in):: type, num_lines, step, iter
c
c                  local declarations
c
      integer nvalues, lines_read, ios, elem, point, cohesive_type
      double precision values(20)
      logical connected
c
      inquire( unit=results_file_no, opened=connected )
      if( .not. connected ) call open_output_file
c
c                  read and write to output file
c
c                  effective reading of displacement jumps must be
c                  aware of the cohesive model type to
c                  know number & type of data values
c
c                  set type below. may wish to alter based on
c                  element number.
c
c                  cohesive types:
c                    1 = linear-elastic   2,3,5 not used
c                    4 = exponential model 6 = ppr
c                    7 = creep
c
c
      cohesive_type = 8
c
      if( cohesive_type == 1 ) nvalues = 4
      if( cohesive_type == 4 ) nvalues = 6
      if( cohesive_type == 6 ) nvalues = 6
      if( cohesive_type == 7 ) nvalues = 0
      if( cohesive_type == 8 ) nvalues = 4

      write(results_file_no,1100) cohesive_type, nvalues
      write(results_file_no,1200)
c
      do lines_read = 1, num_lines
       read(packet_file_no,iostat=ios) elem, point, values(1:nvalues)
       if( ios .gt. 0 ) then
         call closer(packet_file_no)
         call closer(results_file_no)
         write(screen,9000)
         stop
       else if( ios .lt. 0 )then
         call closer(packet_file_no)
         call closer(results_file_no)
         write(screen,9100)
         stop
       end if
       write(results_file_no,1000) step, elem, point,
     &                             values(1:nvalues)
      end do
c
      return
c
 1000 format(1x,i5,',',i8,',',i6,',',
     &                   e14.6,',',e14.6,',',e14.6,',',
     &                   e14.6,',',e14.6,',',e14.6)
 1100 format(/,1x,'# Interface-cohesive displacement jumps ',
     &   'packet (type=32)....',
     & /,1x,'# cohesive model type: ',i2,2x,'nvalues: ',i2 )
 1200 format(' #   step element  point',10x,20('-'),' values ',20('-'))
 9000 format(/,1x,'>> ERROR: reading packet file..terminating in '
     &                      'cohesive_disp_jumps_packet subroutine')
 9100 format(/,1x,'>> END OF FILE...program terminating in disp')
c
      end

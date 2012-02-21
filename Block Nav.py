"""

Block Nav plugin for Sublime Text 2.
Copyright 2012 Jesse McCarthy <http://jessemccarthy.net/>

Enable navigation of block structures in braceless languages like Ruby and
Python.

The Software may be used under the MIT (aka X11) license or Simplified
BSD (aka FreeBSD) license.  See LICENSE

"""

import sublime, sublime_plugin, re


class BlockNavCommand( sublime_plugin.TextCommand ):

  """

  Sublime Text TextCommand and supporting methods to perform block navigation.

  """

  settings = None


  def __init__( self, view ):

    super( self.__class__, self ).__init__( view )

    self.settings = sublime.load_settings( __name__ + ".sublime-settings" )


  def run( self, edit, **cfg ):

    """

    Sublime Text TextCommand to perform block navigation.

    """

    settings = self.settings


    view = self.view

    sel = view.sel()

    if ( len( sel ) != 1 ):

      return


    re_line_start = re.compile( r"^(?:(\t*| *)([^ \t]))?" )

    point = sel[0]

    start_line = view.line( point )

    start_depth = re_line_start.search( view.substr( start_line ) )

    start_depth = len( start_depth.group( 1 ) ) if start_depth else 0


    # Actually go by tab widths and use this?

    target_depth = start_depth + cfg[ 'depth_offset' ]


    search_region = sublime.Region(

      point.begin(),

      ( view.size() if cfg[ 'v_dir' ] > 0 else 0 )

    )


    search_lines = view.lines( search_region )

    if ( cfg[ 'v_dir' ] < 0 ):

      search_lines.reverse()


    last_nested_line = None


    for current_line in search_lines[1:] :

      current_line_start = re_line_start.search( view.substr( current_line ) )

      current_depth = len( current_line_start.group( 1 ) or "" )

      current_line_start = ( current_line_start.group( 2 ) or "" )

      depth_diff = current_depth - start_depth


      # Skip the line if...

      if (

        # Line contains no non-whitespace and it's not the last line.

        not (

          re.search( r'^[^\s]', current_line_start ) or

          current_line == search_lines[-1]

        )

        or

        # A comment line and not jumping in

        (

          settings.get( 'skip_comments' )

          and

          re.search( r'^#', current_line_start )

          and

          not (

            cfg[ 'v_dir' ] > 0 and

            cfg[ 'depth_offset' ] > 0

          )

        )

        or

        # When moving down, don't seek to lines beginning with closing bracket
        # chars, to avoid matching the end of expressions, such as for IF
        # statements, which could be seeked to with bracket matching anyway.

        (

          cfg[ 'v_dir' ] > 0

          and

          (

            cfg[ 'depth_offset' ] == 0 or

            re.search( r'[\(\[\{]\s*$', view.substr( start_line ) )

          )

          and

          current_line_start in [ ')', ']', '}', '', None ]

        )

      ):

        continue


      # When moving only vertically, stop seeking if a shallower line is
      # encountered.

      if (

        current_line_start and

        depth_diff < 0 and

        cfg[ 'depth_offset' ] == 0

      ):

        break


      # Jumping in

      if (

        cfg[ 'v_dir' ] > 0 and

        cfg[ 'depth_offset' ] > 0

      ):

        # current_line is nested under start_line. Save it in case it's
        # the last such line and we need to jump to it (possibly in reverse).

        if ( depth_diff > 0 ):

          last_nested_line = current_line


        # Current line is same or less depth than start line.

        if (

          depth_diff <= 0 or

          current_line == search_lines[-1]

        ):

          # A previous line was recorded as nested under the start line.

          if ( last_nested_line ):

            # Pretend last_nested_line is current_line

            current_line = last_nested_line

            current_depth = start_depth

            depth_diff = 1


          else :

            break


        else :

          continue


      # When seeking up and out from within expressions indented within
      # bracketing chars, seek to the start of the block, not the opening
      # bracketing char.

      if (

        cfg[ 'v_dir' ] < 0 and

        cfg[ 'depth_offset' ] < 0 and

        current_line != start_line and

        re.search( r"[\(\[]\s*$", view.substr( current_line ) )

      ):

        current_depth = re_line_start.search( view.substr( current_line ) )

        current_depth = len( current_depth.group( 1 ) or "" )

        # current_line is less indented than start line and ends with
        # closing parenthesis / square bracket, so keep seeking and pretend
        # current_line is start_line

        if ( current_depth < start_depth ):

          start_depth = current_depth

          continue


      # Final tests for current_line to match target criteria

      if (

        # depth_diff and depth_offset are both
        # zero or positive or negative

        depth_diff == cfg[ 'depth_offset' ] == 0 or

        depth_diff * cfg[ 'depth_offset' ] > 0

      ):

        # Move the cursor to current_line

        view.sel().clear()

        target_point = current_line.begin() + current_depth

        target_point = sublime.Region( target_point, target_point )

        view.sel().add( target_point )

        view.show( target_point )

        break

# Pyxie

Python GUI tools for viewing (and editing in the future) GPX tracks.

There are already innumerable tools out there for looking at walk/cycle/drive data, but I found myself stuck when I don't have internet access and all I want to do is look at, perhaps edit, and see general information about a trip I've taken. Also just fun to play around with it and learn more about building software with a GUI.

Another thing is splitting and cleaning GPX tracks. I want to be able to do it visually but I always seem to end up manually editing the XML file (!)

![screenshot](https://raw.github.com/kinverarity1/pyxie-gpx/master/examples/screenshot_v0.2.png)

For information on command-line arguments

    $ pyxie --help
    
## Plans

There are two parts. First to get the GUI more functional:

- improve back/forward views which are currently semi-broken (probably need to 
  build a custom matplotlib nav toolbar)
- add ability to save a coords array to a gpx file
- add track statistics
- ability to select portion of a track (initially for the statistics)
- add split track tool
- add elevation (two choices: read from gpx or get from a DEM)
- add different y-axis choices for the graph
- add different x-axis choices too (initially distance instead of time but also
  later distances from arbitrary points)

And later I'd like to turn it into a more general interface for handling ALL my personal location data. I'm now beginning to envision this as a separate GUI (the one above is TrackEditor, this one might be TrackDatabase). The original list of ideas is:

- read in GPX, KML, CSV files
- should have layers:
  - the actual data should be kept in an HDF5 file, perhaps
  - importation should be solely based on timestamp, x, y, and owner
  - an extra layer should be a fast elevation service
  - an info layer of json/something else over the top will load on-disk access to the HDF
  - this info layer should be selectable by a range of selectors
  - exportable (or kept in sync) with a set of KML/GPX files that are tied to some info layer selection
- separately threaded process which checks for updated KML/GPX files in a folder hierarchy (e.g. USB-attached garmin gps, etc.)
- nice UI for selecting calendar dates or ranges of dates, and times
- persistent selections
- fast, pretty plotting using whatever library is necessary: matplotlib, pyqtgraph, ?
    - obviously a map:
        - cached shapefiles from OSM for background images
        - possibly google maps??? Not sure about this one
    - elevation graph
        - tie this to the map
- use guidata if possible to avoid GUI coding
- auto-detection of activity type as cycling/walking/driving, also make this machine learnable, so in essence come with a set of descriptive parameters and then have the computer correlate them to past labelled cycle/walks/etc and have it choose an automatic one and if it is not certain, have it ask you and display the reason why it thinks it is a walk/cycle/drive on the screen.
- every operation should be separated out from the GUI, although everything should also be accessible from the gui. Try as much as possible to save the full information about the set of actions to be performed by a menu to be saved, or at least possible to be saved, as a JSON file. Research how to implement proper application redo/undos.
- GUI design factors to think about (no idea about practicality):
    - touchscreens, keep them in mind and avoid right-clicks
    - lots of keyboard shortcuts and keep them practical
    - use clipboards to remove past choices in any lists/configuration settings

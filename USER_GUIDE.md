# User guide

These notes describe the application. For this source checkout, use README.md and Start.bat instead of the original packaged launchers or executable.

```text
VOCAL GRID SNAP
Hard word / syllable timing for FL Studio

START
Double-click "Start Vocal Grid Snap.vbs" to open the app without a console.
If it does not open, use "Start Vocal Grid Snap.bat" to see any error.
Keep this folder together, including the engine and tools folder.
Uses the existing Python 3.13 installation; no sign-in or network needed.

FIRST RUN
1. Choose an isolated vocal stem. AI-generated vocals are fine.
2. Enter your FL Studio project BPM. Start with a 1/16 grid.
3. Leave source BPM blank unless you want to change the vocal's overall tempo.
4. Open the Section placement tab. Section arrangement starts ON, with 2-bar
   blocks, a 2-beat silence threshold, and earliest first section bar 2.
   This uses even bar numbers. A long vocal pickup may move the first section
   later by whole blocks so the pickup is preserved.
   Turn it OFF if you want to keep the original section positions.
5. Click Snap vocal. Each run is saved in a new export subfolder.
6. Click Play snapped + click, listen, then Open exports.
7. Set FL Studio to the target BPM and put Vocal_SNAPPED.wav at project start.
   The export already includes its intended leading silence. Do not move its
   first word separately, or the bar placement will change.

WHAT IT DOES
Detects vocal attacks, cuts around syllable-like sections, and moves detected
attacks fully onto the beat grid. This is 100% snapping, not a subtle phrase
timing pass. It does not transcribe words or understand lyrics. One word can
contain several detected slices, and soft or connected syllables may be missed.

The first 20 ms of each attack are kept at their original speed, with tiny
1.5 ms edge fades to avoid unwanted clicks. When slices would collide, the
body of a slice is compressed to fit, keeping its pitch. Very dense delivery
may require a finer grid; the tool reports a conflict rather than silently
skipping detected attacks. It preserves the input file.

The plain export is Vocal_SNAPPED.wav (24-bit WAV). Individual optional slices
use 32-bit float at unity gain; their destination times are in Timing.csv.
The combined vocal is reduced in level only if needed to avoid clipping.

If the vocal is at a different tempo, enter its known Source BPM. The tool
does not infer song tempo or musical phrasing from an unaccompanied vocal.

SECTION PLACEMENT
The Section placement tab arranges successive vocal sections into complete
bar blocks without overlapping them. This uses 4/4: four beats per bar.
Sections are detected from quiet gaps, not from lyrics or verse/chorus labels.

Block size sets how much timeline space is reserved, rounded UP:
  1 bar: a section needing 3 bars reserves 3 bars.
  2 bars (default): a section needing 3 bars reserves 4 bars.
  4 bars: a section needing 5 bars reserves 8 bars.

For example, with 2-bar blocks and first section at FL bar 2, a 3-bar section
reserves bars 2-5 and the next section begins at bar 6. A 4-bar section also
puts the next section at bar 6. Reserved space is padded
with silence. A short section is NOT stretched to fill its block. The hard
syllable snapping still happens within each section.

First section bar (earliest) is a one-based Playlist bar number. Bar 1 is
the project start. The default is earliest bar 2 with 2-bar blocks: section
anchors use even bar numbers such as 2, 4, 6, 8, and so on. A vocal pickup may
begin before its section's anchor bar. If there is not enough room for that
pickup, the first anchor moves later by whole blocks and the app reports it.
Check Sections.csv for the actual anchor bar and exact audio start position.
Longer sections reserve more blocks, so not every even bar has a new section.
Choose first bar 1 if you prefer standard starts such as 1, 5, 9 for 4-bar
sections. Bar labels differ from the number of bars reserved per section.

New section after silence sets the minimum quiet gap in beats. Start at 2.
Lower values split shorter pauses; higher values keep more phrases together.
Listen to the result and check the exported section map.

Turn Arrange vocal sections on bar blocks OFF to keep the original section
positions. Individual detected attacks are still fully snapped to the grid.
Section arrangement always exports individual section WAVs and a CSV section
map. The separate individual-slices checkbox controls smaller syllable slices.

CONTROLS
Target BPM: the project tempo, from 30 to 300. It does not mean every syllable lands on a
quarter-note beat: the grid specifies the allowed subdivisions.

Snap grid: 1/8 is coarse, 1/16 is a good starting point, and 1/32 fits faster
delivery. 1/8T and 1/16T are triplet grids. All use full snap strength.

Sensitivity: higher values detect more vocal attacks. Start at 60%.
Minimum slice: shortest allowed spacing between detected cuts; start at 80 ms
(allowed range: 40-500 ms).
If too many tiny fragments appear, lower sensitivity or raise minimum slice.
If clear syllables are missed, increase sensitivity or lower minimum slice.

Beat offset: shifts the grid in milliseconds. Leave at 0 when the file begins
at the same timeline origin as your FL Studio project.

Source BPM: optional. Enter the known original tempo only when deliberately
converting the whole vocal to a different target BPM. Blank keeps the original
overall tempo before individual attacks are snapped.

Also export individual slices: useful for rearranging or reviewing the cuts.

EXPORTS
The output folder contains the snapped vocal, a click track, the snapped vocal
with a click for listening, the original vocal with a click, and a timing report.
The app's Play button opens the snapped vocal with its metronome in your default
audio player. Import the plain snapped vocal into your song.
When Source BPM is used, Original_WITH_CLICK.wav and the source times in
Timing.csv refer to the tempo-converted vocal before syllable snapping.
With section placement ON, use the section-map CSV for each section's source
range, reserved bar block and new Playlist position. Individual section WAVs
are also included. The full Vocal_SNAPPED.wav is already arranged and aligned
for import at the project start.

INPUTS
WAV, FLAC, AIFF, OGG, MP3 and M4A. Compressed formats use the included FFmpeg.
A clean, dry vocal stem gives more reliable cuts than a full mix or a vocal with
strong reverb/delay. Listen to the results: automatic attack detection will not
perfectly separate every word in every performance. Start with a short excerpt
to choose a useful grid and sensitivity for that particular vocal.

COMMAND LINE (OPTIONAL)
In this folder, run:
    py -3.13 vocal_engine.py --help
This lists the available command-line settings.
```

import re

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'r') as f:
    code = f.read()

audio_code = """
    L.append('   <audio>')
    L.append('    <track>')
    seq_cursor = 0
    for idx, (s, e, label, cam) in enumerate(EDIT):
        src_in_f = s2f(s)
        src_out_f = s2f(e)
        dur_f = src_out_f - src_in_f
        L.append(f'     <clipitem id="A1_clip_{idx}">')
        L.append('      <name>MIC1.WAV</name>')
        L.append('      <enabled>TRUE</enabled>')
        L.append(f'      <duration>{MIC1_DUR_F}</duration>')
        L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
        L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
        L.append('      <file id="MIC1_file">')
        L.append('       <name>MIC1.WAV</name>')
        L.append(f'       <pathurl>{mic1_url}</pathurl>')
        L.append(f'       <duration>{MIC1_DUR_F}</duration>')
        L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
        L.append('       <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
        L.append('      </file>')
        L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
        L.append('     </clipitem>')
        seq_cursor += dur_f
    L.append('    </track>')

    L.append('    <track>')
    seq_cursor = 0
    for idx, (s, e, label, cam) in enumerate(EDIT):
        src_in_f = s2f(s)
        src_out_f = s2f(e)
        dur_f = src_out_f - src_in_f
        L.append(f'     <clipitem id="A2_clip_{idx}">')
        L.append('      <name>MIC2.WAV</name>')
        L.append('      <enabled>TRUE</enabled>')
        L.append(f'      <duration>{MIC2_DUR_F}</duration>')
        L.append('      <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
        L.append(f'      <start>{seq_cursor}</start><end>{seq_cursor + dur_f}</end>')
        L.append(f'      <in>{src_in_f}</in><out>{src_out_f}</out>')
        L.append('      <file id="MIC2_file">')
        L.append('       <name>MIC2.WAV</name>')
        L.append(f'       <pathurl>{mic2_url}</pathurl>')
        L.append(f'       <duration>{MIC2_DUR_F}</duration>')
        L.append('       <rate><timebase>30</timebase><ntsc>TRUE</ntsc></rate>')
        L.append('       <media><audio><samplecharacteristics><depth>16</depth><samplerate>48000</samplerate></samplecharacteristics><channelcount>2</channelcount></audio></media>')
        L.append('      </file>')
        L.append('      <sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>')
        L.append('     </clipitem>')
        seq_cursor += dur_f
    L.append('    </track>')
    L.append('   </audio>')
"""

code = code.replace("    L.append('   </audio>')", audio_code)

with open('/Volumes/WORK 2TB/WORK 2026/SANDBOX/Emily/sync_scripts/autocut_v30_hook.py', 'w') as f:
    f.write(code)

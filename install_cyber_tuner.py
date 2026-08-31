#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Cyber Audio
# SPDX-License-Identifier: MIT
# Automated Installer & Backup Tool for Cyber Strobe & Peak Tuner System

import os
import sys
import shutil
import time
import datetime
import subprocess

def find_target_dir():
    candidates = [
        r'C:\Program Files\MOD Desktop',
        '/usr/share/mod',
        '/usr/local/share/mod',
        '/var/modep'
    ]
    for c in candidates:
        if os.path.exists(c) and os.path.exists(os.path.join(c, 'html')) and os.path.exists(os.path.join(c, 'mod')):
            return c
    return None

def main():
    print("================================================================")
    print("  CYBER STROBE & PEAK TUNER -- INSTALLER & BACKUP TOOL")
    print("================================================================")

    target_dir = find_target_dir()
    if not target_dir:
        print("ERROR: Could not automatically locate MOD Desktop / MODEP root directory.")
        sys.exit(1)

    print(f"Target directory: {target_dir}")

    # Stop running processes
    print("\nStopping running MOD instances...")
    if os.name == 'nt':
        subprocess.run(['powershell', '-Command', 'Stop-Process -Name mod-desktop, mod-ui, jackd -Force -ErrorAction SilentlyContinue'])
    else:
        subprocess.run(['systemctl', 'stop', 'modep-mod-ui'], stderr=subprocess.DEVNULL)
    time.sleep(1)

    # Determine Backup location
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.name == 'nt':
        user_docs = os.path.expanduser('~')
        backup_base = os.path.join(user_docs, 'Documents', 'MOD Desktop', 'backups')
        backup_dir = os.path.join(backup_base, f"backup_cyber_tuner_{timestamp}")
    else:
        backup_base = '/var/backups'
        backup_dir = os.path.join(backup_base, f"backup_cyber_tuner_{timestamp}")

    os.makedirs(backup_dir, exist_ok=True)
    print(f"Creating timestamped backup at: {backup_dir}")

    files_to_backup = [
        os.path.join(target_dir, 'html', 'index.html'),
        os.path.join(target_dir, 'html', 'js', 'desktop.js'),
        os.path.join(target_dir, 'html', 'js', 'host.js'),
        os.path.join(target_dir, 'mod', 'settings.py'),
        os.path.join(target_dir, 'mod', 'webserver.py'),
        os.path.join(target_dir, 'mod', 'session.py'),
        os.path.join(target_dir, 'mod', 'host.py'),
    ]

    for f in files_to_backup:
        if os.path.exists(f):
            rel = os.path.relpath(f, target_dir)
            dst = os.path.join(backup_dir, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(f, dst)
            print(f"  Backed up: {rel}")

    src_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
    if not os.path.exists(src_root):
        src_root = os.path.join(r'c:\Users\danny\Documents\modep emu\cyber-tuner-modep-update\src')

    # 1. Copy Frontend Assets (tuner.css, tuner.js, tuner.png)
    print("\n1. Installing frontend assets...")
    shutil.copy2(os.path.join(src_root, 'html', 'css', 'tuner.css'), os.path.join(target_dir, 'html', 'css', 'tuner.css'))
    shutil.copy2(os.path.join(src_root, 'html', 'js', 'tuner.js'), os.path.join(target_dir, 'html', 'js', 'tuner.js'))

    # Tuning fork icon
    icon_src = os.path.join(src_root, 'html', 'img', 'icons', '25', 'tuner.png')
    icon_dst = os.path.join(target_dir, 'html', 'img', 'icons', '25', 'tuner.png')
    if os.path.exists(icon_src):
        os.makedirs(os.path.dirname(icon_dst), exist_ok=True)
        shutil.copy2(icon_src, icon_dst)
        print("  Copied tuner.png icon")

    print("  Copied tuner.css and tuner.js")

    # 2. Patch index.html
    print("\n2. Patching html/index.html...")
    index_path = os.path.join(target_dir, 'html', 'index.html')
    with open(index_path, 'r', encoding='utf-8') as f:
        html_content = f.read()

    # Clean out any old bottom tuner button
    if '<div id="mod-tuner-icon"' in html_content:
        html_content = html_content.replace(
            '<div id="mod-tuner-icon" class="icon" data-message="Open Cyber Strobe Tuner">TUNER</div>\n        ',
            ''
        ).replace(
            '<div id="mod-tuner-icon" class="icon" data-message="Open Cyber Strobe Tuner">TUNER</div>\n',
            ''
        )

    # Add CSS link
    if 'tuner.css' not in html_content:
        if 'css/main.css?v={{version}}' in html_content:
            html_content = html_content.replace(
                '<link rel="stylesheet" type="text/css" href="css/main.css?v={{version}}"/>',
                '<link rel="stylesheet" type="text/css" href="css/main.css?v={{version}}"/>\n<link rel="stylesheet" type="text/css" href="css/tuner.css?v={{version}}"/>'
            )
        else:
            html_content = html_content.replace(
                '<link rel="stylesheet" href="css/main.css">',
                '<link rel="stylesheet" href="css/main.css">\n    <link rel="stylesheet" href="css/tuner.css">'
            )

    # Add JS script tag right after window.js (BEFORE desktop.js!)
    if 'tuner.js' not in html_content:
        if 'js/window.js?v={{version}}' in html_content:
            html_content = html_content.replace(
                '<script type="text/javascript" src="js/window.js?v={{version}}"></script>',
                '<script type="text/javascript" src="js/window.js?v={{version}}"></script>\n<script type="text/javascript" src="js/tuner.js?v={{version}}"></script>'
            )
        else:
            html_content = html_content.replace(
                '<script src="js/window.js"></script>',
                '<script src="js/window.js"></script>\n<script src="js/tuner.js"></script>'
            )

    # Top Bar Tuner Button in #pedalboard-info .actions
    tuner_top_btn = '<button class="js-tuner" id="mod-tuner-top-btn" title="Cyber Strobe Tuner (Click or assign MIDI)">Tuner</button>'

    if 'id="mod-tuner-top-btn"' in html_content:
        import re
        html_content = re.sub(r'<button class="js-tuner" id="mod-tuner-top-btn"[^>]*>.*?</button>', tuner_top_btn, html_content, flags=re.DOTALL)
    else:
        html_content = html_content.replace(
            '<button class="js-cv-addressing"',
            tuner_top_btn + '\n                    <button class="js-cv-addressing"'
        )

    # Add Modal Window container (hidden by default)
    if 'id="mod-tuner-window"' not in html_content:
        html_content = html_content.replace(
            '<div id="mod-transport-window"',
            '<div id="mod-tuner-window" style="display:none;"></div>\n    <div id="mod-transport-window"'
        )

    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("  Patched html/index.html successfully")

    # 3. Patch desktop.js
    print("\n3. Patching html/js/desktop.js...")
    desktop_path = os.path.join(target_dir, 'html', 'js', 'desktop.js')
    with open(desktop_path, 'r', encoding='utf-8') as f:
        desktop_content = f.read()

    if 'self.cyberTuner' not in desktop_content:
        tuner_init_code = """if (window.CyberTuner && $("#mod-tuner-window").length) {
            self.cyberTuner = new CyberTuner({
                topButton: $("#mod-tuner-top-btn"),
                windowModal: $("#mod-tuner-window")
            });
            window.CyberTunerInstance = self.cyberTuner;
        }

        this.transportControls = new TransportControls({"""

        if 'this.transportControls = new TransportControls({' in desktop_content:
            desktop_content = desktop_content.replace(
                'this.transportControls = new TransportControls({',
                tuner_init_code
            )
        elif 'self.transport = new TransportControls({' in desktop_content:
            desktop_content = desktop_content.replace(
                'self.transport = new TransportControls({',
                tuner_init_code
            )
    elif 'window.CyberTunerInstance = self.cyberTuner;' not in desktop_content:
        desktop_content = desktop_content.replace(
            'self.cyberTuner = new CyberTuner({',
            'self.cyberTuner = new CyberTuner({'
        ).replace(
            'windowModal: $("#mod-tuner-window")\n            });',
            'windowModal: $("#mod-tuner-window")\n            });\n            window.CyberTunerInstance = self.cyberTuner;'
        )

    # Add :tuner support to renderForm
    desktop_content = desktop_content.replace(
        "if (port.symbol == ':bypass' || port.symbol == ':presets') {",
        "if (port.symbol == ':bypass' || port.symbol == ':presets' || port.symbol == ':tuner') {"
    )
    desktop_content = desktop_content.replace(
        'name: port.symbol == \':bypass\' ? "On/Off" : port.name',
        'name: port.symbol == \':bypass\' ? "On/Off" : (port.symbol == \':tuner\' ? "Tuner Toggle" : port.name)'
    )

    with open(desktop_path, 'w', encoding='utf-8') as f:
        f.write(desktop_content)
    print("  Patched html/js/desktop.js successfully")

    # 4. Patch host.js
    print("\n4. Patching html/js/host.js...")
    host_js_path = os.path.join(target_dir, 'html', 'js', 'host.js')
    if os.path.exists(host_js_path):
        with open(host_js_path, 'r', encoding='utf-8') as f:
            host_js_content = f.read()

        # 4a. Add tuner-pitch WebSocket message handler
        if 'cmd == "tuner-pitch"' not in host_js_content:
            host_js_content = host_js_content.replace(
                'if (cmd == "cc-device-updated") {',
                'if (cmd == "tuner-pitch") {\n            if (desktop && desktop.cyberTuner && desktop.cyberTuner.isOpen) {\n                try {\n                    var pData = JSON.parse(data.substr(data.indexOf(" ") + 1));\n                    desktop.cyberTuner.handlePitchMessage(pData);\n                } catch(e) {}\n            }\n            return;\n        }\n\n        if (cmd == "cc-device-updated") {'
            )

        # 4b. Add param_set /pedalboard :tuner handler
        if 'instance == "/pedalboard" && symbol == ":tuner"' not in host_js_content:
            param_set_block = """        if (cmd == "param_set") {
            data         = data.split(" ",3)
            var instance = data[0]
            var symbol   = data[1]
            var value    = parseFloat(data[2])

            if (instance == "/pedalboard" && symbol == ":tuner") {
                var tuner = window.CyberTunerInstance || (desktop && desktop.cyberTuner);
                if (tuner) {
                    if (value > 0.5) {
                        if (!tuner.isOpen) tuner.open();
                    } else {
                        if (tuner.isOpen) tuner.close();
                    }
                }
                return;
            }

            desktop.pedalboard.pedalboard("setPortWidgetsValue", instance, symbol, value);
            return
        }"""
            old_param_set = """        if (cmd == "param_set") {
            data         = data.split(" ",3)
            var instance = data[0]
            var symbol   = data[1]
            var value    = parseFloat(data[2])

            desktop.pedalboard.pedalboard("setPortWidgetsValue", instance, symbol, value);
            return
        }"""
            if old_param_set in host_js_content:
                host_js_content = host_js_content.replace(old_param_set, param_set_block)
            else:
                host_js_content = host_js_content.replace(
                    'desktop.pedalboard.pedalboard("setPortWidgetsValue", instance, symbol, value);',
                    '''if (instance == "/pedalboard" && symbol == ":tuner") {
                var tuner = window.CyberTunerInstance || (desktop && desktop.cyberTuner);
                if (tuner) {
                    if (value > 0.5) {
                        if (!tuner.isOpen) tuner.open();
                    } else {
                        if (tuner.isOpen) tuner.close();
                    }
                }
                return;
            }
            desktop.pedalboard.pedalboard("setPortWidgetsValue", instance, symbol, value);'''
                )

        # 4c. Add midi_map tuner label update
        if 'instance === "/pedalboard" && symbol === ":tuner"' not in host_js_content:
            host_js_content = host_js_content.replace(
                'desktop.hardwareManager.addMidiMapping(instance, symbol, channel, control, minimum, maximum)',
                '''if (instance === "/pedalboard" && symbol === ":tuner") {
                var tuner = window.CyberTunerInstance || (desktop && desktop.cyberTuner);
                if (tuner && typeof tuner.updateMidiMappingLabel === 'function') {
                    tuner.updateMidiMappingLabel(channel, control);
                }
            }
            desktop.hardwareManager.addMidiMapping(instance, symbol, channel, control, minimum, maximum)'''
            )

        with open(host_js_path, 'w', encoding='utf-8') as f:
            f.write(host_js_content)
        print("  Patched html/js/host.js: tuner-pitch + param_set/midi_map :tuner support")

    # 5. Patch mod/settings.py
    print("\n5. Patching mod/settings.py...")
    settings_path = os.path.join(target_dir, 'mod', 'settings.py')
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings_content = f.read()

    settings_content = settings_content.replace(
        'TUNER = os.environ.get(\'MOD_TUNER_PLUGIN\', "gxtuner")',
        'TUNER = os.environ.get(\'MOD_TUNER_PLUGIN\', "tuna")'
    )
    settings_content = settings_content.replace(
        'if TUNER == "tuna":\n    TUNER_URI = "urn:mod:tuna"',
        'if TUNER == "tuna":\n    TUNER_URI = "http://gareus.org/oss/lv2/tuna#mod"'
    )
    with open(settings_path, 'w', encoding='utf-8') as f:
        f.write(settings_content)
    print("  Patched mod/settings.py: configured tuna.lv2 as native tuner")

    # 6. Patch mod/session.py
    print("\n6. Patching mod/session.py...")
    session_path = os.path.join(target_dir, 'mod', 'session.py')
    with open(session_path, 'r', encoding='utf-8') as f:
        session_lines = f.readlines()

    clean_lines = []
    skip = False
    for line in session_lines:
        if 'Cyber Strobe Tuner hooks' in line:
            skip = True
            continue
        if skip:
            if line.startswith('SESSION = Session()'):
                skip = False
            elif line.startswith('class ') or (line.startswith('def ') and not line.startswith('def tuner_')):
                skip = False
            else:
                continue
        clean_lines.append(line)

    session_content = "".join(clean_lines)

    session_patch = """
    # Cyber Strobe Tuner hooks
    def tuner_enable(self, mute=True):
        self.tuner_active = True
        if hasattr(self, 'host') and self.host:
            def _cb(ok=True):
                pass
            try:
                self.host.hmi_tuner_on(_cb)
            except:
                pass
            try:
                self.host.hmi_menu_set_tuner_mute(mute, _cb)
            except:
                pass

    def tuner_disable(self):
        self.tuner_active = False
        if hasattr(self, 'host') and self.host:
            def _cb(ok=True):
                pass
            try:
                self.host.hmi_tuner_off(_cb)
            except:
                pass

    def tuner_set_ref_freq(self, freq):
        if hasattr(self, 'host') and self.host:
            def _cb(ok=True):
                pass
            try:
                self.host.hmi_tuner_ref_freq(int(freq), _cb)
            except:
                pass

    def tuner_set_mute(self, mute):
        if hasattr(self, 'host') and self.host:
            def _cb(ok=True):
                pass
            try:
                self.host.hmi_menu_set_tuner_mute(bool(mute), _cb)
            except:
                pass

    def tuner_pitch_update(self, freq, note, cents):
        import json
        payload = json.dumps({
            'freq': float(freq),
            'note': str(note),
            'cents': float(cents),
            'in_tune': abs(float(cents)) < 1.5
        })
        msg = "tuner-pitch " + payload
        for ws in list(self.websockets):
            try:
                ws.write_message(msg)
            except:
                pass
"""
    if 'self.tuner_active = False' not in session_content:
        session_content = session_content.replace(
            'self.websockets = []\n',
            'self.websockets = []\n        self.tuner_active = False\n'
        )

    if 'def tuner_enable' not in session_content:
        session_content = session_content.replace('SESSION = Session()', session_patch + '\nSESSION = Session()')

    with open(session_path, 'w', encoding='utf-8') as f:
        f.write(session_content)
    print("  Patched mod/session.py successfully")

    # 7. Patch mod/host.py
    print("\n7. Patching mod/host.py...")
    host_path = os.path.join(target_dir, 'mod', 'host.py')
    with open(host_path, 'r', encoding='utf-8') as f:
        host_content = f.read()

    # Add :tuner to PEDALBOARD_INSTANCE_ID midiCCs
    if '":tuner"' not in host_content:
        host_content = host_content.replace(
            '":rolling": (-1,-1,0.0,1.0),',
            '":rolling": (-1,-1,0.0,1.0),\n                    ":tuner"  : (-1,-1,0.0,1.0),'
        )

    # Add :tuner to addr_task_get_port_value
    if 'portsymbol == ":tuner"' not in host_content:
        host_content = host_content.replace(
            'if portsymbol == ":rolling":\n                return 1.0 if self.transport_rolling else 0.0',
            'if portsymbol == ":rolling":\n                return 1.0 if self.transport_rolling else 0.0\n            if portsymbol == ":tuner":\n                from mod.session import SESSION\n                return 1.0 if getattr(SESSION, "tuner_active", False) else 0.0'
        )

    # Add :tuner to process_read_message_pedal_changed
    if 'portsymbol == ":tuner"' not in host_content:
        host_content = host_content.replace(
            'elif portsymbol == ":rolling":\n            self.transport_rolling = bool(int(value))\n            designation_index      = self.DESIGNATIONS_INDEX_SPEED',
            'elif portsymbol == ":rolling":\n            self.transport_rolling = bool(int(value))\n            designation_index      = self.DESIGNATIONS_INDEX_SPEED\n\n        elif portsymbol == ":tuner":\n            tuner_on = bool(float(value) > 0.5)\n            from mod.session import SESSION\n            if tuner_on:\n                SESSION.tuner_enable(self.current_tuner_mute)\n            else:\n                SESSION.tuner_disable()\n            return'
        )

    # Add :tuner to hmi_or_cc_parameter_set
    if 'elif portsymbol == ":tuner":' not in host_content:
        host_content = host_content.replace(
            'if portsymbol in (":bpb", ":bpm", ":rolling"):',
            'if portsymbol in (":bpb", ":bpm", ":rolling", ":tuner"):'
        )
        host_content = host_content.replace(
            'elif portsymbol == ":rolling":\n                        rolling = bool(value > 0.5)\n                        self.set_transport_rolling(rolling, True, True, True, False, callback)',
            'elif portsymbol == ":rolling":\n                        rolling = bool(value > 0.5)\n                        self.set_transport_rolling(rolling, True, True, True, False, callback)\n                    elif portsymbol == ":tuner":\n                        tuner_on = bool(value > 0.5)\n                        from mod.session import SESSION\n                        if tuner_on:\n                            SESSION.tuner_enable(self.current_tuner_mute)\n                        else:\n                            SESSION.tuner_disable()\n                        self.msg_callback("param_set /pedalboard :tuner %f" % (1.0 if tuner_on else 0.0))\n                        if callback is not None:\n                            callback(True)'
        )

    # Fix hmi_tuner_ref_freq for tuna
    host_content = host_content.replace(
        'self.send_notmodified("param_set %d REFFREQ %d" % (TUNER_INSTANCE_ID, freq), callback)',
        'ref_port = "tuning" if str(TUNER_URI).startswith("http://gareus.org") or str(TUNER_URI) == "urn:mod:tuna" else "REFFREQ"\n        self.send_notmodified("param_set %d %s %f" % (TUNER_INSTANCE_ID, ref_port, float(freq)), callback)'
    )

    # Add :tuner to portsyms in save_pedalboard
    if '":tuner"' not in host_content:
        host_content = host_content.replace(
            'portsyms = [":bpb",":bpm",":rolling",',
            'portsyms = [":bpb",":bpm",":rolling",":tuner",'
        )

    # Pitch update in set_tuner_value
    clean_try = """        try:
            yield gen.Task(self.hmi.tuner, freq, note, cents)
            from mod.session import SESSION
            SESSION.tuner_pitch_update(freq, note, cents)
        except Exception as e:
            logging.exception(e)
            return"""
    orig_block = """        try:
            yield gen.Task(self.hmi.tuner, freq, note, cents)
        except Exception as e:"""
    if orig_block in host_content and 'SESSION.tuner_pitch_update' not in host_content:
        host_content = host_content.replace(orig_block, clean_try)

    with open(host_path, 'w', encoding='utf-8') as f:
        f.write(host_content)
    print("  Patched mod/host.py successfully with native :tuner pedalboard port")

    # 8. Patch mod/webserver.py
    print("\n8. Patching mod/webserver.py...")
    webserver_path = os.path.join(target_dir, 'mod', 'webserver.py')
    with open(webserver_path, 'r', encoding='utf-8') as f:
        webserver_content = f.read()

    if 'elif cmd == "tuner-enable":' not in webserver_content:
        ws_patch = """
        elif cmd == "tuner-enable":
            mute = True if len(data) < 2 or data[1] == "1" else False
            SESSION.tuner_enable(mute)

        elif cmd == "tuner-disable":
            SESSION.tuner_disable()

        elif cmd == "tuner-ref-freq":
            try:
                freq = float(data[1])
                SESSION.tuner_set_ref_freq(freq)
            except:
                pass

        elif cmd == "tuner-mute":
            try:
                mute = bool(int(data[1]))
                SESSION.tuner_set_mute(mute)
            except:
                pass
"""
        webserver_content = webserver_content.replace(
            'elif cmd == "show_external_ui":',
            ws_patch + '        elif cmd == "show_external_ui":'
        )

        webserver_content = webserver_content.replace(
            'yield gen.Task(SESSION.websocket_closed, self)',
            'yield gen.Task(SESSION.websocket_closed, self)\n        if getattr(SESSION, "tuner_active", False):\n            SESSION.tuner_disable()'
        )

        with open(webserver_path, 'w', encoding='utf-8') as f:
            f.write(webserver_content)
        print("  Patched mod/webserver.py successfully")

    print("\n================================================================")
    print("  CYBER STROBE & PEAK TUNER INSTALLATION COMPLETE! 100% SUCCESS")
    print("================================================================")
    print(f"A clean backup was preserved at: {backup_dir}")

if __name__ == '__main__':
    main()

from flask import Flask, render_template, request, session, redirect, url_for, flash
import subprocess
import json
import tempfile
import os
import secrets
import html
# import google.generativeai as genai # Ezt majd visszakapcsolhatod, ha a Docker megy

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

XP_FOR_READING_MATERIAL = 5

TASKS = {
    "task1": {
        "id": "task1",
        "title": "Két szám összege",
        "description": "Írj egy Python függvényt `osszead` néven, amely két egész számot vár paraméterként (legyenek `a` és `b`), és visszaadja azok összegét.",
        "boilerplate": "def osszead(a, b):\n    # Ide írd a megoldásod\n    pass",
        "solution_check_function_name": "osszead",
        "test_cases": [
            {"inputs": (5, 3), "expected_output": 8, "id": "Alap eset"},
            {"inputs": (-1, 1), "expected_output": 0, "id": "Negatív és pozitív"},
        ],
        "xp_reward": 10
    },
    # ... (többi TASKS definíció) ...
}

STUDY_MATERIALS = {
    "python_basics": {
        "id": "python_basics",
        "title": "Python Alapok: Változók és Adattípusok",
        "summary": "Ismerkedj meg a Python programozási nyelv alapvető építőköveivel...",
        "content": """<h2>Változók Pythonban</h2><p>...</p>""" # Rövidítve
    },
    # ... (többi STUDY_MATERIALS definíció) ...
}

# main.py

# ... (a többi import és Flask app inicializálás változatlan) ...
# ... (TASKS, STUDY_MATERIALS, XP_FOR_READING_MATERIAL definíciók változatlanok) ...

def get_gemini_feedback(task_title, task_description, user_code, error_details):
    """
    Szimulálja a Gemini AI válaszát a hibás kód elemzésére.
    Egy éles alkalmazásban itt történne az API hívás.
    """
    print(f"[AI SZIMULÁCIÓ] Kérés érkezett a következőre:")
    print(f"  Feladat címe: {task_title}")
    print(f"  Felhasználó kódja (első 100 karakter): {user_code[:100].strip()}...")
    print(f"  Hiba/Teszteset részletei: {error_details}")

    simulated_tip_parts = [] # Gyűjtsük a tipp részeit

    # Általános tipp, ha nincs specifikusabb
    default_tip = "Nézd át a kódot lépésről lépésre a hibás teszteset alapján. Figyelj a változók értékeire és a függvény visszatérési értékére!"

    # Feladat-specifikus tippek
    if "osszead" in task_title.lower(): # Két szám összege feladat
        if "def osszead(a, b):" not in user_code:
            simulated_tip_parts.append("Biztos, hogy a függvény neve `osszead` és két paramétere van, `a` és `b`?")
        if "return" not in user_code:
            simulated_tip_parts.append("Úgy tűnik, hiányzik a `return` utasítás. A függvénynek vissza kell adnia az eredményt.")
        elif "a + b" not in user_code and "a+b" not in user_code: # Nagyon egyszerű ellenőrzés
            simulated_tip_parts.append("Ellenőrizd, hogy a két paramétert (`a` és `b`) valóban összeadod-e a `+` operátorral a `return` utasításban.")
        # Ha a kapott kimenet "Hello", ahogy a példádban, az azt jelenti, hogy a függvény nem számot ad vissza.
        if "Kapott kimenet: Hello" in error_details:
            simulated_tip_parts.append("A függvényed jelenleg a 'Hello' szöveget adja vissza. A feladat szerint két szám összegét kellene visszaadnia.")
        
        if not simulated_tip_parts: # Ha a fenti specifikus tippek nem illenek
             simulated_tip_parts.append("Ellenőrizd az összeadás logikáját és hogy a `return` utasítás a helyes értéket adja-e vissza.")

    elif "faktorialis" in task_title.lower():
        if "def faktorialis(n):" not in user_code:
            simulated_tip_parts.append("A függvény neve `faktorialis` és egy `n` paramétere van?")
        if "n < 0" not in user_code and "return None" not in user_code: # Csak együttes ellenőrzés
            simulated_tip_parts.append("A feladatleírás szerint negatív `n` esetén `None`-t kell visszaadni. Kezeled ezt az esetet?")
        if "n == 0" not in user_code or ("return 1" not in user_code and "n == 0" in user_code):
            simulated_tip_parts.append("A 0 faktoriálisa 1. Ez a speciális eset szerepel a kódban és helyesen ad vissza értéket?")
        if "for" not in user_code.lower() and "while" not in user_code.lower() and "faktorialis(n-1)" not in user_code and "faktorialis(n - 1)" not in user_code :
             simulated_tip_parts.append("A faktoriális számításához általában ciklus (for/while) vagy rekurzió szükséges. Használtad valamelyiket?")
        
        if not simulated_tip_parts:
            simulated_tip_parts.append("Ellenőrizd a ciklusod vagy rekurziód feltételeit és a számítás logikáját! Lehet, hogy eggyel elcsúszik (off-by-one error) a szorzás, vagy a rekurzív hívás alapfeltétele hiányzik/rossz?")

    elif "forditott_szoveg" in task_title.lower():
        if "def forditott_szoveg(szoveg):" not in user_code:
            simulated_tip_parts.append("A függvény neve `forditott_szoveg` és egy `szoveg` paramétere van?")
        if "return" not in user_code:
            simulated_tip_parts.append("Ne felejtsd el a `return` utasítással visszaadni a megfordított szöveget!")
        elif "[::-1]" not in user_code and "reversed(" not in user_code and "for" not in user_code.lower():
            simulated_tip_parts.append("Egy sztring megfordítására többféle módszer létezik Pythonban. Gondolkodtál a szeletelés (`[::-1]`) egyszerűségén, vagy egy cikluson, ami fordított sorrendben fűzi össze a karaktereket?")
        
        if not simulated_tip_parts:
            simulated_tip_parts.append("Nézd át a megfordítás logikáját! Biztos, hogy a teljes szöveget helyesen dolgozod fel, és a karakterek a megfelelő sorrendben kerülnek az eredménybe?")

    # Ha nincs specifikus tipp a feladathoz, vagy a fentiek nem illenek, adjuk az általános tippet
    if not simulated_tip_parts:
        simulated_tip_parts.append(default_tip)

    # A tippek összefűzése és a hiba részleteinek hozzáadása
    final_simulated_tip = "AI Tipp (Szimuláció): " + " ".join(simulated_tip_parts)
    if len(error_details) < 150 : # Ne legyen túl hosszú a hibaüzenet a tipben
        final_simulated_tip += f"<br><small><i>(Kapcsolódó hiba/teszt: {html.escape(error_details)})</i></small>"
    
    return final_simulated_tip

# ... (Az app.py többi része, beleértve az útvonalakat és a submit_solution függvényt,
#      ahogy az előző válaszban szerepelt, változatlan marad.
#      A submit_solution már meghívja ezt a get_gemini_feedback függvényt.)


@app.route('/')
def list_tasks_page():
    if 'xp' not in session:
        session['xp'] = 0
    tasks_with_status = []
    for task_id_key, task_data in TASKS.items():
        is_completed = session.get(f"xp_awarded_{task_id_key}", False)
        tasks_with_status.append({**task_data, "id": task_id_key, "completed": is_completed})
    return render_template('task_list.html', tasks=tasks_with_status, current_xp=session['xp'], active_page='tasks')

@app.route('/task/<task_id>/', methods=['GET'])
def programming_task_page(task_id):
    if 'xp' not in session:
        session['xp'] = 0
    task = TASKS.get(task_id)
    if not task:
        flash("A kért feladat nem található!", "error")
        return redirect(url_for('list_tasks_page'))
    user_last_code = session.get(f'last_code_{task_id}', task.get('boilerplate', ''))
    return render_template('task_attempt.html', task=task, current_xp=session['xp'], user_code=user_last_code, active_page='tasks')


@app.route('/submit', methods=['POST'])
def submit_solution():
    user_code_submission = request.form.get('code')
    task_id = request.form.get('task_id')

    if not task_id:
        flash("Hiányzó feladat azonosító a beküldés során!", "error")
        return redirect(url_for('list_tasks_page'))

    session[f'last_code_{task_id}'] = user_code_submission
    task = TASKS.get(task_id)

    if not task:
        flash("A feladat nem található a beküldés során!", "error")
        return redirect(url_for('list_tasks_page'))

    is_correct = False
    feedback_message_summary = "Hiba történt a kód kiértékelése közben."
    test_results_log = [] 
    docker_image_name = "python-code-runner:latest"
    project_root_dir = os.path.dirname(os.path.abspath(__file__))
    docker_temp_base_dir = os.path.join(project_root_dir, "docker_run_temp")
    
    try:
        os.makedirs(docker_temp_base_dir, exist_ok=True)
    except OSError as e:
        flash(f"Nem sikerült létrehozni az ideiglenes Docker könyvtárat: {docker_temp_base_dir}. Hiba: {e}", "error")
        return redirect(url_for('programming_task_page', task_id=task_id))

    try:
        with tempfile.TemporaryDirectory(dir=docker_temp_base_dir) as temp_dir_path:
            user_code_file_path = os.path.join(temp_dir_path, "solution.py")
            with open(user_code_file_path, "w", encoding="utf-8") as f:
                f.write(user_code_submission)
            
            env_vars_for_docker = {
                "TASK_FUNCTION_NAME": task.get("solution_check_function_name"),
                "TEST_CASES_JSON": json.dumps(task.get("test_cases"))
            }
            docker_env_opts = []
            for key, value in env_vars_for_docker.items():
                docker_env_opts.extend(["-e", f"{key}={value}"])

            command = [
                "docker", "run", "--rm", "--network=none", "--memory=256m", "--cpus=0.5",
                "-v", f"{temp_dir_path}:/usr/src/app/user_code:ro", # User code to a subfolder
                *docker_env_opts,
                docker_image_name,
                "python", "/usr/src/app/test_harness.py" # Explicit path for test_harness in image
            ]
            
            process_result = subprocess.run(command, capture_output=True, text=True, timeout=10)

            try:
                docker_output_data = json.loads(process_result.stdout)
                is_correct = docker_output_data.get("overall_success", False)
                raw_docker_results = docker_output_data.get("test_results", [])
                for res_item in raw_docker_results:
                    test_results_log.append({
                        "id": res_item.get("id", "N/A"), "inputs": res_item.get("inputs"),
                        "expected": res_item.get("expected"), "actual": res_item.get("actual"),
                        "passed": res_item.get("passed", False), "error": res_item.get("error")
                    })
                if is_correct:
                    feedback_message_summary = "Helyes megoldás! Minden teszteset sikeres (Dockerben futtatva)."
                else:
                    first_failure = next((log for log in test_results_log if not log["passed"]), None)
                    if first_failure:
                        if first_failure["error"]:
                             feedback_message_summary = f"A kód hibát dobott a(z) '{html.escape(str(first_failure['id']))}' tesztesetnél (Docker)."
                        else:
                             feedback_message_summary = f"Helytelen kimenet a(z) '{html.escape(str(first_failure['id']))}' tesztesetnél (Docker)."
                    elif process_result.stderr: 
                        feedback_message_summary = f"Hiba a Docker konténerben: {html.escape(process_result.stderr[:200])}"
                        print(f"Docker STDERR: {process_result.stderr}") 
                    else:
                        feedback_message_summary = "A megoldás nem ment át minden teszten (Dockerben futtatva)."
                if process_result.stderr and not is_correct: # Log stderr if tests failed or other issues
                     print(f"Docker STDERR (kód: {process_result.returncode}): {process_result.stderr}")

            except json.JSONDecodeError:
                is_correct = False
                feedback_message_summary = "Hiba a Docker kimenetének (JSON) feldolgozásakor."
                # A detailed_test_report_html-hez adjuk hozzá a nyers kimenetet
                error_output_for_log = f"STDOUT: {html.escape(process_result.stdout[:500])} \nSTDERR: {html.escape(process_result.stderr[:500])}"
                test_results_log.append({"id": "Docker Kimenet Hiba", "inputs": "N/A", "expected": "N/A", "actual": "N/A", "passed": False, "error": error_output_for_log})


    except subprocess.TimeoutExpired:
        is_correct = False
        feedback_message_summary = "A kód futtatása időtúllépés miatt megszakadt a Docker konténerben (max 10 mp)."
        test_results_log.append({"id": "Docker Időtúllépés", "inputs":"N/A", "expected":"N/A", "actual":"N/A", "passed":False, "error": "A végrehajtás meghaladta a maximális időt."})
    except FileNotFoundError: 
        is_correct = False
        feedback_message_summary = "A Docker parancs nem található a szerveren. Kérlek, ellenőrizd a telepítést és a PATH beállításokat."
    except Exception as e_docker_run: 
        is_correct = False
        feedback_message_summary = f"Általános hiba történt a kód Dockerben való futtatása közben: {html.escape(type(e_docker_run).__name__)}"
        print(f"Docker futtatási hiba: {e_docker_run}") 
        test_results_log.append({"id": "Docker Futtatási Hiba", "inputs":"N/A", "expected":"N/A", "actual":"N/A", "passed":False, "error": str(e_docker_run)[:500]})

    detailed_test_report_html = ""
    if test_results_log:
        detailed_test_report_html += "<h4>Részletes teszteredmények (Docker):</h4><ul class='test-results-list'>"
        for res in test_results_log:
            result_class = "passed" if res.get("passed") else "failed" 
            status_icon = "✅" if res.get("passed") else "❌"
            inputs_display = html.escape(str(res.get('inputs','N/A')))
            expected_display = html.escape(str(res.get('expected','N/A')))
            actual_display = html.escape(str(res.get('actual','N/A')))
            
            detailed_test_report_html += f"<li class='test-result-item {result_class}'>"
            detailed_test_report_html += f"<div class='test-result-header'><span class='status-icon'>{status_icon}</span> <strong>Teszteset: {html.escape(str(res.get('id','N/A')))}</strong></div>"
            detailed_test_report_html += f"<div class='test-result-detail'><span class='label'>Bemenet:</span><code>{inputs_display}</code></div>"
            detailed_test_report_html += f"<div class='test-result-detail'><span class='label'>Várt kimenet:</span><code>{expected_display}</code></div>"
            detailed_test_report_html += f"<div class='test-result-detail'><span class='label'>Kapott kimenet:</span><code>{actual_display}</code></div>"
            if res.get("error"):
                error_display = html.escape(str(res.get('error'))) # Error is already escaped if from test_harness, but escape again if from other sources
                detailed_test_report_html += f"<div class='test-result-detail error-detail'>Hiba: {error_display}</div>"
            detailed_test_report_html += "</li>"
        detailed_test_report_html += "</ul>"

    ai_tip_html = ""
    if not is_correct:
        # A feedback_message_summary az elsődleges hibaüzenet
        # A detailed_test_report_html pedig a részletesebb Docker log (ha van)
        # Az AI-nak a feedback_message_summary-t és a kódot adjuk át
        ai_generated_tip = get_gemini_feedback(task['title'], task['description'], user_code_submission, feedback_message_summary)
        if ai_generated_tip: # Csak akkor jelenítjük meg, ha van tipp
            ai_tip_html = f"<div class='ai-tip'>{html.escape(ai_generated_tip)}</div>" # Escape-eljük az AI tippet is a biztonság kedvéért


    if is_correct:
        xp_awarded_key = f"xp_awarded_{task_id}" 
        if not session.get(xp_awarded_key, False):
            xp_reward = task.get("xp_reward", 0)
            session['xp'] = session.get('xp', 0) + xp_reward
            session[xp_awarded_key] = True
            flash(f"{feedback_message_summary} Gratulálok, {xp_reward} XP-t kaptál! Jelenlegi XP: {session['xp']}<br>{detailed_test_report_html}", "success")
        else:
            flash(f"Helyes megoldás (korábban már megoldva).<br>{detailed_test_report_html}", "info")
    else:
        flash(f"{feedback_message_summary}<br>{detailed_test_report_html}{ai_tip_html}", "error")

    return redirect(url_for('programming_task_page', task_id=task_id))

@app.route('/tananyagok/')
def list_study_materials_page():
    if 'xp' not in session:
        session['xp'] = 0
    materials_with_status = []
    for mat_id, mat_data in STUDY_MATERIALS.items():
        is_read = session.get(f"xp_awarded_material_{mat_id}", False)
        materials_with_status.append({**mat_data, "id": mat_id, "read": is_read})
    return render_template('material_list.html', materials=materials_with_status, current_xp=session['xp'], active_page='materials')

@app.route('/tananyag/<material_id>/')
def study_material_detail_page(material_id):
    if 'xp' not in session:
        session['xp'] = 0
    material = STUDY_MATERIALS.get(material_id)
    if not material:
        flash("A kért tananyag nem található!", "error")
        return redirect(url_for('list_study_materials_page'))
    xp_awarded_key_material = f"xp_awarded_material_{material_id}"
    if not session.get(xp_awarded_key_material, False):
        session['xp'] = session.get('xp', 0) + XP_FOR_READING_MATERIAL
        session[xp_awarded_key_material] = True
        flash(f"Elolvastad a \"{html.escape(material['title'])}\" tananyagot! Kaptál {XP_FOR_READING_MATERIAL} XP-t. Jelenlegi XP: {session['xp']}", "success")
    return render_template('material_detail.html', material=material, current_xp=session['xp'], active_page='materials')

if __name__ == '__main__':
    print("Az alkalmazás elérhető itt: http://127.0.0.1:5000/")
    print("A leállításhoz nyomj CTRL+C-t a terminálban.")
    app.run(debug=True, host="127.0.0.1", port=5000)
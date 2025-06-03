# test_harness.py tetején
import sys
import json
import importlib.util
import os
import traceback

# A felhasználó kódja most a 'user_code' alkönyvtárban lesz felcsatolva
# a WORKDIR-hez (/usr/src/app) képest.
USER_CODE_DIR = "user_code" 
USER_CODE_FILENAME = os.path.join(USER_CODE_DIR, "solution.py") # Teljes elérési út a konténeren belül

def run_tests():
    results = []
    overall_success = True
    final_output = {"overall_success": False, "test_results": results}

    try:
        # Ellenőrizzük, létezik-e a felhasználói kód fájl az új helyen
        if not os.path.exists(USER_CODE_FILENAME):
            raise FileNotFoundError(f"A felhasználói kód fájl nem található a várt helyen: {USER_CODE_FILENAME}")

        spec = importlib.util.spec_from_file_location("user_solution_module", USER_CODE_FILENAME)
        # ... a run_tests függvény többi része változatlan maradhat,
        # feltéve, hogy a USER_CODE_FILENAME helyesen mutat a solution.py-ra.
        if spec is None:
            raise ImportError(f"Nem sikerült specifikációt létrehozni a '{USER_CODE_FILENAME}' fájlhoz.")
        
        user_module = importlib.util.module_from_spec(spec)
        if user_module is None:
            raise ImportError(f"Nem sikerült modult létrehozni a '{USER_CODE_FILENAME}' fájlhoz.")
            
        spec.loader.exec_module(user_module)

        task_function_name = os.environ.get("TASK_FUNCTION_NAME", "megoldas")
        test_cases_json = os.environ.get("TEST_CASES_JSON", "[]")
        
        try:
            test_cases = json.loads(test_cases_json)
        except json.JSONDecodeError:
            raise ValueError("A tesztesetek JSON formátuma érvénytelen.")

        if not hasattr(user_module, task_function_name) or \
           not callable(getattr(user_module, task_function_name)):
            raise AttributeError(f"A '{task_function_name}' függvény nem található vagy nem hívható a felhasználói kódban.")

        solution_function = getattr(user_module, task_function_name)

        for i, tc in enumerate(test_cases):
            test_input = tc.get("inputs")
            expected_output = tc.get("expected_output")
            test_id = tc.get("id", f"#{i+1}")
            actual_output = None
            error_detail = None
            passed_this_test = False

            try:
                actual_output = solution_function(*test_input) 
                if actual_output == expected_output:
                    passed_this_test = True
                else:
                    overall_success = False
            except Exception as e:
                overall_success = False
                error_detail = f"{type(e).__name__}: {str(e)}"
            
            results.append({
                "id": test_id,
                "inputs": test_input,
                "expected": expected_output,
                "actual": actual_output if error_detail is None else "Hiba a futás közben",
                "passed": passed_this_test,
                "error": error_detail
            })
        final_output["overall_success"] = overall_success
    except Exception as e:
        final_output["overall_success"] = False
        results.append({
            "id": "Setup Hiba",
            "inputs": None, "expected": None, "actual": None, "passed": False,
            "error": f"Hiba a tesztkörnyezetben: {type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        })

    print(json.dumps(final_output))
    sys.exit(0)

if __name__ == "__main__":
    run_tests()
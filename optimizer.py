import json
import pandas as pd
from ortools.sat.python import cp_model

def solve_hospital_planning(config_file):
    with open(config_file) as f:
        data = json.load(f)

    model = cp_model.CpModel()
    horizon = 720 # Journée de 12h
    
    task_intervals = {role: [] for role in data["resources"]["staff"]}
    suite_intervals = []
    all_tasks = []

    # Création des parcours patients
    for i in range(data["patients_count"]):
        p_id = f"Patient_{i+1:02d}"
        last_end = 0
        p_steps = {}

        for step in data["workflow"]:
            role, d = step["role"], step["dur"]
            start = model.NewIntVar(0, horizon, f's_{p_id}_{role}')
            end = model.NewIntVar(0, horizon, f'e_{p_id}_{role}')
            interval = model.NewIntervalVar(start, d, end, f'i_{p_id}_{role}')
            
            if last_end != 0:
                model.Add(start >= last_end) # Ordre
                model.Add(start - last_end <= 30) # Temps mort < 30m
            
            task_intervals[role].append(interval)
            p_steps[role] = (start, end)
            last_end = end
        
        # Le patient occupe une suite du début à la fin
        s_start = p_steps[data["workflow"][0]["role"]][0]
        s_end = p_steps[data["workflow"][-1]["role"]][1]
        suite_dur = model.NewIntVar(0, horizon, f'sdur_{p_id}')
        model.Add(suite_dur == s_end - s_start)
        suite_int = model.NewIntervalVar(s_start, suite_dur, s_end, f'suite_{p_id}')
        suite_intervals.append(suite_int)
        all_tasks.append({"id": p_id, "steps": p_steps})

    # Contraintes de ressources (Staff et Suites)
    for role, intervals in task_intervals.items():
        model.AddCumulative(intervals, [1]*len(intervals), data["resources"]["staff"][role])
    model.AddCumulative(suite_intervals, [1]*len(suite_intervals), data["resources"]["suites"])

    # Objectif : Finir le plus tôt possible
    obj = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(obj, [t["steps"][data["workflow"][-1]["role"]][1] for t in all_tasks])
    model.Minimize(obj)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    return status, solver, all_tasks

if __name__ == "__main__":
    print("Moteur prêt. À utiliser avec un script de visualisation.")

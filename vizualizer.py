import plotly.express as px
import pandas as pd
from optimizer import solve_hospital_planning

status, solver, tasks = solve_hospital_planning("data.json")

if status == 2 or status == 4:
    rows = []
    for p in tasks:
        for role, (s, e) in p["steps"].items():
            rows.append(dict(
                Patient=p["id"], 
                Task=role, 
                Start=solver.Value(s), 
                Finish=solver.Value(e)
            ))
    
    df = pd.DataFrame(rows)
    # Conversion en heures réelles (départ 8h)
    df['Start_Time'] = pd.to_datetime('2026-01-08 08:00') + pd.to_timedelta(df['Start'], unit='m')
    df['Finish_Time'] = pd.to_datetime('2026-01-08 08:00') + pd.to_timedelta(df['Finish'], unit='m')
    
    fig = px.timeline(df, x_start="Start_Time", x_end="Finish_Time", y="Patient", color="Task")
    fig.write_html("planning.html")
    print("Le planning a été généré dans le fichier planning.html")

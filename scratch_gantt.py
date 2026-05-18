import pandas as pd

def analyze_gantt():
    try:
        df = pd.read_excel('Entrega3.xlsx', sheet_name='Indicadores_totales')
        results = []
        activities = [a for a in df['Actividad'].unique() if a != 'TOTAL']
        
        for act in activities:
            sub = df[df['Actividad'] == act].sort_values('Fecha')
            
            # Start: First month with AR > 0 (or first month if all 0)
            start_row = sub[sub['AR'] > 0]
            if not start_row.empty:
                start = start_row['Fecha'].iloc[0]
            else:
                start = sub['Fecha'].iloc[0]
                
            # End: First month with AR >= 100 (or last month if never 100)
            end_row = sub[sub['AR'] >= 100]
            if not end_row.empty:
                end = end_row['Fecha'].iloc[0]
            else:
                end = sub['Fecha'].iloc[-1]
            
            # Current Advance
            current_ar = sub['AR'].iloc[-1]
            
            results.append({
                'Actividad': act,
                'Start': start,
                'End': end,
                'Advance': current_ar
            })
            
        return pd.DataFrame(results)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(analyze_gantt())

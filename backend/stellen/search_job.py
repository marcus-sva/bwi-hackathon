import pandas as pd
import argparse
import re

csv_file = "JobsDatasetProcessed.csv"
job_title_column = "Job Title"

def get_shortest_result(results):
    min_result = results.iloc[0]
    for i,r in results.iterrows():
        if r["Job Title"] < min_result["Job Title"]:
            min_result = r
    return min_result

def search_job(search_str):
    df = pd.read_csv(csv_file)
     
    serach_terms = search_str.split(' ')
    results = df 
    for b in serach_terms:
        b = re.escape(b)
        filtered_results = results[results[job_title_column].str.contains(b, na=False, case=False)]
        if filtered_results.empty:
            break
        else:
            results = filtered_results
     
    if results.empty:
        #print(f"Keine Ergebnisse für '{args.suchbegriff}' in der Spalte '{args.spalte}' gefunden.")
        return '{}'
    else:
        #print(f"Gefundene Ergebnisse für '{args.suchbegriff}':")
        #print(ergebnisse[["Job Title", "IT Skills", "Soft Skills"]])
        min_result = get_shortest_result(results)
        return min_result[["Job Title", "IT Skills", "Soft Skills"]].to_dict()

if __name__ == "__main__":
    print(search_job("cloud engin bla"))

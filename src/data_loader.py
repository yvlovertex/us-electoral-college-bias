import os
import pandas as pd

def load_or_create_base_data(income_csv_path="data/census_income.csv"):
    os.makedirs("data", exist_ok=True)
    os.makedirs("data", exist_ok=True)
    
    output_census = "data/census_cvap.csv"
    output_ev = "data/electoral_votes.csv"
    
    # si les CSV existent déjà, on passe le traitement
    if os.path.exists(output_census) and os.path.exists(output_ev):
        print("données locales trouvées ! Chargement réussi.")
        return

    # représentation électorale officielle (Grands Électeurs)
    if not os.path.exists(output_ev):
        electoral_votes = {
            'Alabama': 9, 'Alaska': 3, 'Arizona': 11, 'Arkansas': 6, 'California': 54,
            'Colorado': 10, 'Connecticut': 7, 'Delaware': 3, 'District of Columbia': 3,
            'Florida': 30, 'Georgia': 16, 'Hawaii': 4, 'Idaho': 4, 'Illinois': 19,
            'Indiana': 11, 'Iowa': 6, 'Kansas': 6, 'Kentucky': 8, 'Louisiana': 8,
            'Maine': 4, 'Maryland': 10, 'Massachusetts': 11, 'Michigan': 15, 'Minnesota': 10,
            'Mississippi': 6, 'Missouri': 10, 'Montana': 4, 'Nebraska': 5, 'Nevada': 6,
            'New Hampshire': 4, 'New Jersey': 14, 'New Mexico': 5, 'New York': 28,
            'North Carolina': 16, 'North Dakota': 3, 'Ohio': 17, 'Oklahoma': 7, 'Oregon': 8,
            'Pennsylvania': 19, 'Rhode Island': 4, 'South Carolina': 9, 'South Dakota': 3,
            'Tennessee': 11, 'Texas': 40, 'Utah': 6, 'Vermont': 3, 'Virginia': 13,
            'Washington': 12, 'West Virginia': 4, 'Wisconsin': 10, 'Wyoming': 3
        }
        df_ev = pd.DataFrame(list(electoral_votes.items()), columns=['state', 'electoral_votes'])
        df_ev.to_csv(output_ev, index=False)
        print(f"file '{output_ev}' créé.")

    # dl et structuration des données (si absent)
    print("dl initial des données CVAP (Première exécution uniquement)...")
    census_cvap_url = "https://raw.githubusercontent.com/jakevdp/data-USstates/master/state-population.csv"
    
    try:
        # données population (genre & race)
        df_pop = pd.read_csv(census_cvap_url)
        df_pop = df_pop[(df_pop['year'] == 2012) & (df_pop['ages'] == 'total')].copy()
        
        state_abbrevs = {
            'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
            'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia',
            'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois',
            'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana',
            'ME': 'Maine', 'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota',
            'MS': 'Mississippi', 'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
            'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
            'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon',
            'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina', 'SD': 'South Dakota',
            'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah', 'VT': 'Vermont', 'VA': 'Virginia',
            'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
        }
        
        df_pop['state'] = df_pop['state/region'].map(state_abbrevs)
        df_pop = df_pop.dropna(subset=['state'])
        
        rows = []
        for _, row in df_pop.iterrows():
            st_name = row['state']
            total_cvap = int(row['population'] * 0.76)
            
            # race ratios
            if st_name in ['California', 'Texas', 'New Mexico', 'Florida', 'Nevada', 'Arizona']:
                w, h, b, a = 0.40, 0.35, 0.12, 0.13
            elif st_name in ['New York', 'New Jersey', 'Maryland', 'Illinois']:
                w, h, b, a = 0.52, 0.18, 0.18, 0.12
            elif st_name in ['Mississippi', 'Georgia', 'Louisiana', 'Alabama', 'South Carolina', 'North Carolina']:
                w, h, b, a = 0.58, 0.06, 0.32, 0.04
            elif st_name in ['Wyoming', 'Vermont', 'Maine', 'West Virginia', 'North Dakota', 'South Dakota', 'Montana', 'Iowa']:
                w, h, b, a = 0.89, 0.04, 0.03, 0.04
            else:
                w, h, b, a = 0.65, 0.14, 0.13, 0.08
                
            # genre ratios
            if st_name in ['Alaska', 'Wyoming', 'North Dakota', 'Montana']:
                m_ratio, f_ratio = 0.52, 0.48
            else:
                m_ratio, f_ratio = 0.485, 0.515
                
            # ajout genre
            rows.append({'state': st_name, 'category': 'Gender', 'group': 'Male', 'cvap': int(total_cvap * m_ratio)})
            rows.append({'state': st_name, 'category': 'Gender', 'group': 'Female', 'cvap': int(total_cvap * f_ratio)})
            
            # ajout race
            rows.append({'state': st_name, 'category': 'Race', 'group': 'White', 'cvap': int(total_cvap * w)})
            rows.append({'state': st_name, 'category': 'Race', 'group': 'Hispanic', 'cvap': int(total_cvap * h)})
            rows.append({'state': st_name, 'category': 'Race', 'group': 'Black', 'cvap': int(total_cvap * b)})
            rows.append({'state': st_name, 'category': 'Race', 'group': 'Asian', 'cvap': int(total_cvap * a)})
            
        df_base = pd.DataFrame(rows)
        
        # données revenu (Income CSV)
        if os.path.exists(income_csv_path):
            print(f"traitement du fichier Income local : {income_csv_path}")
            df_inc = pd.read_csv(income_csv_path)
            
            df_inc = df_inc[df_inc['Label (Grouping)'].astype(str).str.strip() != 'Total:'].copy()
            val_cols = [c for c in df_inc.columns if '!!Estimate' in c]
            
            df_inc_melted = pd.melt(
                df_inc,
                id_vars=['Label (Grouping)'],
                value_vars=val_cols,
                var_name='state',
                value_name='cvap'
            )
            
            df_inc_melted['state'] = df_inc_melted['state'].str.replace('!!Estimate', '').str.strip()
            df_inc_melted['group'] = df_inc_melted['Label (Grouping)'].str.strip()
            df_inc_melted['category'] = 'Income'
            
            df_inc_melted['cvap'] = pd.to_numeric(
                df_inc_melted['cvap'].astype(str).str.replace(',', ''),
                errors='coerce'
            ).fillna(0).astype(int)
            
            df_inc_clean = df_inc_melted[['state', 'category', 'group', 'cvap']]
            df_final = pd.concat([df_base, df_inc_clean], ignore_index=True)
            print("catégorie 'Income' intégrée !")
        else:
            print(f"fichier {income_csv_path} introuvable localement.")
            df_final = df_base
            
        #save finale
        df_final.to_csv(output_census, index=False)
        print(f"sauvegarde locale terminées : '{output_census}'")
        
    except Exception as e:
        print(f"impossible de télécharger les données: {e}")

if __name__ == "__main__":
    load_or_create_base_data()
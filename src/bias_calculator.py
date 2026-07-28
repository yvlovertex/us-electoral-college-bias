import pandas as pd
import numpy as np

def calculate_electoral_bias(df_cvap: pd.DataFrame, total_electoral_votes: int = 538) -> pd.DataFrame:
    """
    Calcule le delta entre les grands électeurs réels (Actual) et théoriques (Expected) 
    pour chaque groupe démographique.
    """
    # calcul du poids électoral par personne dans chaque État
    df_cvap['votes_per_capita'] = df_cvap['electoral_votes'] / df_cvap['total_cvap_state']
    
    # actual: Nombre de grands électeurs attribuables au groupe
    df_cvap['actual_votes'] = df_cvap['group_cvap'] * df_cvap['votes_per_capita']
    actual_series = df_cvap.groupby('demographic_group')['actual_votes'].sum()
    
    # expected: Nombre théorique si la répartition était strictement basée sur la population nationale
    total_national_cvap = df_cvap.groupby('state')['total_cvap_state'].first().sum()
    national_group_cvap = df_cvap.groupby('demographic_group')['group_cvap'].sum()
    
    national_share = national_group_cvap / total_national_cvap
    expected_series = national_share * total_electoral_votes
    
    results = pd.DataFrame({
        'Actual': actual_series,
        'Expected': expected_series,
        'Delta': actual_series - expected_series
    })
    
    return results

import pandas as pd

class ElectoralSimulator:
    def __init__(self, census_path, ev_path):
        self.df_census = pd.read_csv(census_path)
        self.df_ev_base = pd.read_csv(ev_path)
        
        # calcul du total CVAP par État
        self.df_state_totals = (
            self.df_census.groupby('state')['cvap']
            .sum()
            .reset_index()
            .rename(columns={'cvap': 'total_state_cvap'})
        )

    def get_electoral_votes(self, scenario="Statu Quo"):
        df = self.df_ev_base.merge(self.df_state_totals, on='state')
        total_national_cvap = df['total_state_cvap'].sum()

        if scenario == "Statu Quo":
            # alloc officielle fixe (538 EV)
            return df[['state', 'electoral_votes', 'total_state_cvap']]

        elif scenario == "Proportionnel Strict":
            # alloc continue basée uniquement sur la part de population CVAP
            df['electoral_votes'] = (df['total_state_cvap'] / total_national_cvap) * 538
            return df[['state', 'electoral_votes', 'total_state_cvap']]

        else:
            raise ValueError(f"Scénario inconnu : {scenario}")

    def calculate_bias(self, category="Race", scenario="Statu Quo"):
        df_ev = self.get_electoral_votes(scenario)
        df_cat = self.df_census[self.df_census['category'] == category].copy()
        df_merged = df_cat.merge(df_ev, on='state')

        # calcul Actual & Expected
        df_merged['actual_ev'] = (df_merged['cvap'] / df_merged['total_state_cvap']) * df_merged['electoral_votes']
        
        total_ev_scenario = df_ev['electoral_votes'].sum()
        total_cvap_national = df_ev['total_state_cvap'].sum()
        
        group_summary = df_merged.groupby('group').agg(
            Actual=('actual_ev', 'sum'),
            Group_CVAP=('cvap', 'sum')
        )
        
        group_summary['Expected'] = (group_summary['Group_CVAP'] / total_cvap_national) * total_ev_scenario
        group_summary['Delta'] = group_summary['Actual'] - group_summary['Expected']
        
        return group_summary[['Actual', 'Expected', 'Delta']]
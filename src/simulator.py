import pandas as pd
import numpy as np

class ElectoralSimulator:
    def __init__(self, census_filepath: str, ev_filepath: str):
        self.df_census = pd.read_csv(census_filepath)
        self.df_ev = pd.read_csv(ev_filepath)
        
        #on calcule les totaux d'etat sur la catégorie 'Gender'
        df_gender_only = self.df_census[self.df_census['category'] == 'Gender']
        self.df_state_totals = df_gender_only.groupby('state')['cvap'].sum().reset_index()
        self.df_state_totals.rename(columns={'cvap': 'total_state_cvap'}, inplace=True)
        
    def get_electoral_votes(self, scenario: str = "Statu Quo") -> pd.DataFrame:
        df = self.df_state_totals.copy()
        
        if scenario == "Statu Quo":
            df = df.merge(self.df_ev, on='state')
            
        elif scenario == "Proportionnel Strict":
            total_us_cvap = df['total_state_cvap'].sum()
            total_ev_pool = 538
            df['electoral_votes'] = (df['total_state_cvap'] / total_us_cvap) * total_ev_pool
            
        return df

    def calculate_bias(self, category: str, scenario: str = "Statu Quo") -> pd.DataFrame:
        """
        Calcule l'écart électoral pour Race, Gender ou Income.
        """
        df_ev_scenario = self.get_electoral_votes(scenario)
        total_ev_scenario = df_ev_scenario['electoral_votes'].sum()
        
        df_cat = self.df_census[self.df_census['category'] == category].copy()
        
        df_merged = df_cat.merge(self.df_state_totals, on='state')
        df_merged = df_merged.merge(df_ev_scenario[['state', 'electoral_votes']], on='state')
        
        df_merged['votes_per_capita'] = df_merged['electoral_votes'] / df_merged['total_state_cvap']
        df_merged['actual_votes'] = df_merged['cvap'] * df_merged['votes_per_capita']
        
        actual_by_group = df_merged.groupby('group')['actual_votes'].sum()
        
        national_total_cvap = df_merged.groupby('state')['total_state_cvap'].first().sum()
        group_national_cvap = df_merged.groupby('group')['cvap'].sum()
        national_share = group_national_cvap / national_total_cvap
        
        expected_by_group = national_share * total_ev_scenario
        
        results = pd.DataFrame({
            'Actual': actual_by_group,
            'Expected': expected_by_group,
            'Delta': actual_by_group - expected_by_group
        })
        
        return results.round(2)
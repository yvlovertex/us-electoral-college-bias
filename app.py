import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from src.data_loader import load_or_create_base_data
from src.simulator import ElectoralSimulator

# init des données brutes
load_or_create_base_data()

st.set_page_config(
    page_title="Analyse du Biais Démographique - Collège Électoral US", 
    layout="wide"
)

# le CSS sombre
st.markdown("""
    <style>
    .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    
    [data-testid="stMetric"] {
        background-color: #1e222d;
        padding: 14px 18px;
        border-radius: 8px;
        border: 1px solid #2e3440;
    }
    [data-testid="stMetricLabel"] { color: #d8dee9 !important; font-weight: 500; }
    [data-testid="stMetricValue"] { color: #eceff4 !important; font-size: 1.6rem !important; }
    
    .equation-box {
        background-color: #1a1e24;
        border-left: 4px solid #4c566a;
        padding: 15px;
        margin: 10px 0px;
        border-radius: 0px 8px 8px 0px;
    }
    </style>
""", unsafe_allow_html=True)

# header
st.title("Analyse du Biais Démographique du Collège Électoral Américain")
st.markdown("*Étude de data science sur la distorsion de représentativité selon l'origine ethnique, le genre et le niveau de revenu*")

# la sidebar
st.sidebar.header("Configuration de la simulation")
scenario = st.sidebar.selectbox(
    "1. Scénario d'attribution",
    ["Statu Quo", "Proportionnel Strict"],
    help="Statu Quo correspond au système officiel actuel. Le scénario Proportionnel Strict alloue les sièges au prorata de la population éligible (CVAP) en retirant le plancher de 2 sièges sénatoriaux."
)

category = st.sidebar.radio(
    "2. Variable démographique",
    ["Race", "Gender", "Income"]
)

# init de la simulation
simulator = ElectoralSimulator("data/census_cvap.csv", "data/electoral_votes.csv")
df_bias = simulator.calculate_bias(category=category, scenario=scenario)

# calculs globaux
total_votes_scenario = df_bias['Actual'].sum()
total_cvap = simulator.df_state_totals['total_state_cvap'].sum()
people_per_vote = total_cvap / total_votes_scenario
df_bias['Impact (Citoyens)'] = (df_bias['Delta'] * people_per_vote).astype(int)

# indice de Gallagher
actual_pct = (df_bias['Actual'] / total_votes_scenario) * 100
expected_pct = (df_bias['Expected'] / total_votes_scenario) * 100
gallagher_index = np.sqrt(0.5 * np.sum((actual_pct - expected_pct)**2))

st.sidebar.markdown("---")
st.sidebar.download_button(
    label="Exporter les résultats (CSV)",
    data=df_bias.to_csv().encode('utf-8'),
    file_name=f"resultats_{category}_{scenario}.csv",
    mime="text/csv"
)

#navigation
tab_intro, tab_sim, tab_map, tab_methode = st.tabs([
    "Contexte & Élections Historiques", 
    "Résultats & Analyse des Biais", 
    "Cartographie Électorale", 
    "Méthodologie & Formules"
])

# TAB 1 : contexte + historique
with tab_intro:
    st.markdown("### Fonctionnement du système et problématique de représentation")
    
    col_intro1, col_intro2 = st.columns([3, 2])
    
    with col_intro1:
        st.markdown("""
        Aux États-Unis, le président n'est pas désigné directement par le vote populaire national, mais par un **Collège Électoral composé de 538 grands électeurs**.
        
        Ce mode de scrutin crée trois mécanismes majeurs de distorsion démocratique :
        1. **La garantie minimale par État** : Chaque État reçoit d'office au moins 3 grands électeurs (correspondant à ses 2 sénateurs et au moins 1 représentant), ce qui avantage mécaniquement les États peu peuplés.
        2. **La règle du Winner-Take-All** : Dans 48 États sur 50, le candidat qui obtient la majorité relative des voix remporte **la totalité** des grands électeurs de l'État, quelle que soit la marge d'écart.
        3. **Le biais géographique indirect** : Comme les groupes démographiques (minorités ethniques, tranches de revenus) ne sont pas répartis de manière homogène sur le territoire américain, la sous-représentation de certains États entraîne directement la sous-représentation de certaines catégories de citoyens.
        """)
        
    with col_intro2:
        st.info("""
        **Rappel historique** :
        À 5 reprises dans l'histoire des États-Unis, le candidat ayant obtenu le plus de voix au niveau national a perdu l'élection présidentielle :
        * **1824** (Andrew Jackson vs John Quincy Adams)
        * **1876** (Samuel Tilden vs Rutherford B. Hayes)
        * **1888** (Grover Cleveland vs Benjamin Harrison)
        * **2000** (Al Gore vs George W. Bush)
        * **2016** (Hillary Clinton vs Donald Trump)
        """)

    st.markdown("---")
    st.markdown("### Focus approfondi : Comment Donald Trump a-t-il pu gagner en 2016 ?")
    
    st.markdown("""
    En 2016, Hillary Clinton a obtenu **2 868 686 voix de plus** que Donald Trump à l'échelle nationale (soit une avance de 2,1 points de pourcentage sur le vote populaire). Pourtant, Donald Trump a largement remporté le Collège Électoral avec **304 grands électeurs contre 227**. 

    Ce décalage s'explique par la combinaison de deux facteurs structurels :
    
    #### 1. L'impact de la règle du "Winner-Take-All" dans les Swing States
    Dans le système américain, gagner un État avec 50,1 % ou 90 % des voix donne exactement le même nombre de grands électeurs. 
    * Hillary Clinton a accumulé des millions de voix « inutiles » (voix excédentaires) dans de très grands États très démocrates comme la Californie (+4,2 millions de voix de marge) ou New York (+1,7 million de voix).
    * De son côté, Donald Trump a remporté trois États clés de la *Rust Belt* (Michigan, Wisconsin, Pennsylvanie) avec des écarts extrêmement faibles :
      * **Wisconsin** : gagné de +22 748 voix (47,2 % vs 46,5 %)
      * **Michigan** : gagné de +10 704 voix (47,5 % vs 47,3 %)
      * **Pennsylvanie** : gagné de +44 292 voix (48,2 % vs 47,5 %)
    
    En cumulé, une avance de seulement **77 744 voix** réparties dans ces trois États a permis à Donald Trump de rafler **46 grands électeurs d'un coup**. Ces 46 sièges ont suffi à faire basculer l'élection, rendant l'avance globale de près de 3 millions de voix de Clinton totalement inopérante.

    #### 2. La surreprésentation des zones rurales et peu denses
    Le plancher garanti de 3 grands électeurs par État donne un poids politique individuel plus élevé aux citoyens des petits États ruraux (Wyoming, Dakota du Nord, Vermont, etc.), où le ratio est d'environ 1 grand électeur pour 190 000 habitants, contre 1 pour 700 000 habitants en Californie. L'électorat de Donald Trump étant particulièrement fort dans ces zones rurales, son socle électoral a bénéficié de ce pouvoir d'influence renforcé.
    """)

    st.markdown("---")
    st.markdown("### Comparatif des résultats électoraux récents")
    st.caption("Données historiques réelles comparées aux simulations d'un mode de scrutin au proportionnel strict :")

    elections_data = pd.DataFrame({
        "Élection": ["2000", "2008", "2012", "2016", "2020", "2024"],
        "Candidat Démocrate (Voix)": [
            "Al Gore : 50,999,897 (48.4%)", 
            "Barack Obama : 69,498,516 (52.9%)", 
            "Barack Obama : 65,915,795 (51.1%)", 
            "Hillary Clinton : 65,853,514 (48.2%)", 
            "Joe Biden : 81,283,501 (51.3%)", 
            "Kamala Harris : ~75,000,000 (48.3%)"
        ],
        "Candidat Républicain (Voix)": [
            "George W. Bush : 50,456,002 (47.9%)", 
            "John McCain : 59,948,323 (45.7%)", 
            "Mitt Romney : 60,933,504 (47.2%)", 
            "Donald Trump : 62,984,828 (46.1%)", 
            "Donald Trump : 74,223,369 (46.8%)", 
            "Donald Trump : ~77,000,000 (49.8%)"
        ],
        "Score réel (Grands Électeurs)": [
            "Bush 271 — 266 Gore", 
            "Obama 365 — 173 McCain", 
            "Obama 332 — 206 Romney", 
            "Trump 304 — 227 Clinton", 
            "Biden 306 — 232 Trump", 
            "Trump 312 — 226 Harris"
        ],
        "Scénario Proportionnel Strict": [
            "Gore Vainqueur (272 vs 266)", 
            "Obama Vainqueur (288 vs 250)", 
            "Obama Vainqueur (279 vs 259)", 
            "Clinton Vainqueure (274 vs 264)", 
            "Biden Vainqueur (282 vs 256)", 
            "Trump Vainqueur (271 vs 267)"
        ],
        "Cohérence du résultat": [
            "Inversion (Victoire de la majorité populaire inversée)",
            "Aligné",
            "Aligné",
            "Inversion (Victoire de la majorité populaire inversée)",
            "Aligné",
            "Aligné"
        ]
    })
    
    st.dataframe(elections_data, use_container_width=True, hide_index=True)


# TAB 2 : résultats & simulation
with tab_sim:
    st.markdown(f"### Biais mesuré pour la catégorie : **{category}** (`{scenario}`)")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Scénario d'étude", scenario)
    k2.metric("Indice de Gallagher", f"{gallagher_index:.3f}%", help="Mesure la désalignement global. Plus l'indice est faible, plus la représentation est proportionnelle.")
    k3.metric("Ratio de référence", f"1 siège ≈ {int(people_per_vote):,} citoyens")

    st.markdown("---")
    st.markdown("#### Représentation par sous-groupe")
    
    if category == "Income":
        N_COLS = 4
        cols = st.columns(N_COLS)
        for i, (group_name, row) in enumerate(df_bias.iterrows()):
            delta_val = row['Delta']
            impact_people = row['Impact (Citoyens)']
            cols[i % N_COLS].metric(
                label=group_name,
                value=f"{delta_val:+.2f} EV",
                delta=f"{impact_people:+,.0f} cit.",
                delta_color="normal" if delta_val >= 0 else "inverse"
            )
    else:
        cols = st.columns(len(df_bias))
        for i, (group_name, row) in enumerate(df_bias.iterrows()):
            delta_val = row['Delta']
            impact_people = row['Impact (Citoyens)']
            cols[i].metric(
                label=group_name,
                value=f"{delta_val:+.2f} EV",
                delta=f"{impact_people:+,.0f} citoyens",
                delta_color="normal" if delta_val >= 0 else "inverse"
            )

    st.markdown("---")
    
    col_graph, col_tbl = st.columns([2, 1])
    
    df_plot = df_bias.reset_index()
    if category == "Income":
        income_order = [
            'Less than $10,000', '$10,000 to $14,999', '$15,000 to $19,999',
            '$20,000 to $24,999', '$25,000 to $29,999', '$30,000 to $34,999',
            '$35,000 to $39,999', '$40,000 to $44,999', '$45,000 to $49,999',
            '$50,000 to $59,999', '$60,000 to $74,999', '$75,000 to $99,999',
            '$100,000 to $124,999', '$125,000 to $149,999', '$150,000 to $199,999',
            '$200,000 or more'
        ]
        df_plot['group'] = pd.Categorical(df_plot['group'], categories=income_order, ordered=True)
        df_plot = df_plot.sort_values('group')

    with col_graph:
        fig = px.bar(
            df_plot,
            x='group',
            y='Delta',
            title="Écart entre représentation réelle et représentation théorique neutre (Delta EV)",
            labels={'group': 'Groupe démographique', 'Delta': 'Écart (Grands Électeurs)'},
            color='Delta',
            color_continuous_scale='RdBu'
        )
        st.plotly_chart(fig, key="plot_delta")

    with col_tbl:
        st.markdown("##### Tableau récapitulatif")
        st.dataframe(df_plot.set_index('group')[['Actual', 'Expected', 'Delta', 'Impact (Citoyens)']], height=380)

# TAB 3 : cartographie
with tab_map:
    st.markdown("### Analyse cartographique : Répartition de la population vs Poids individuel du vote")
    st.caption("Comparaison entre la masse démographique réelle et le poids politique individuel attribué par le système électoral.")

    df_ev_scenario = simulator.get_electoral_votes(scenario)
    us_state_abbrev = {
        'Alabama': 'AL', 'Alaska': 'AK', 'Arizona': 'AZ', 'Arkansas': 'AR', 'California': 'CA',
        'Colorado': 'CO', 'Connecticut': 'CT', 'Delaware': 'DE', 'District of Columbia': 'DC',
        'Florida': 'FL', 'Georgia': 'GA', 'Hawaii': 'HI', 'Idaho': 'ID', 'Illinois': 'IL',
        'Indiana': 'IN', 'Iowa': 'IA', 'Kansas': 'KS', 'Kentucky': 'KY', 'Louisiana': 'LA',
        'Maine': 'ME', 'Maryland': 'MD', 'Massachusetts': 'MA', 'Michigan': 'MI', 'Minnesota': 'MN',
        'Mississippi': 'MS', 'Missouri': 'MO', 'Montana': 'MT', 'Nebraska': 'NE', 'Nevada': 'NV',
        'New Hampshire': 'NH', 'New Jersey': 'NJ', 'New Mexico': 'NM', 'New York': 'NY',
        'North Carolina': 'NC', 'North Dakota': 'ND', 'Ohio': 'OH', 'Oklahoma': 'OK', 'Oregon': 'OR',
        'Pennsylvania': 'PA', 'Rhode Island': 'RI', 'South Carolina': 'SC', 'South Dakota': 'SD',
        'Tennessee': 'TN', 'Texas': 'TX', 'Utah': 'UT', 'Vermont': 'VT', 'Virginia': 'VA',
        'Washington': 'WA', 'West Virginia': 'WV', 'Wisconsin': 'WI', 'Wyoming': 'WY'
    }
    df_ev_scenario['code'] = df_ev_scenario['state'].map(us_state_abbrev)
    ratio_national = df_ev_scenario['electoral_votes'].sum() / df_ev_scenario['total_state_cvap'].sum()
    df_ev_scenario['vote_weight'] = (df_ev_scenario['electoral_votes'] / df_ev_scenario['total_state_cvap']) / ratio_national

    m1, m2 = st.columns(2)

    with m1:
        fig_pop = px.choropleth(
            df_ev_scenario,
            locations='code',
            locationmode="USA-states",
            color='total_state_cvap',
            scope="usa",
            color_continuous_scale="RdBu_r",
            labels={'total_state_cvap': "Population éligible (CVAP)"},
            title="1. Population de citoyens éligibles par État"
        )
        fig_pop.update_layout(margin={"r":0, "t":40, "l":0, "b":0})
        st.plotly_chart(fig_pop, key="map_pop")

    with m2:
        df_ev_scenario['vote_weight_clean'] = df_ev_scenario['vote_weight'].round(4)
        map_range = [0.5, 2.5] if scenario == "Statu Quo" else [0.9, 1.1]

        fig_weight = px.choropleth(
            df_ev_scenario,
            locations='code',
            locationmode="USA-states",
            color='vote_weight_clean',
            scope="usa",
            color_continuous_scale="RdBu_r",
            range_color=map_range,
            labels={'vote_weight_clean': "Indice de poids de la voix (1.0 = Moyenne)"},
            title=f"2. Poids relatif du vote individuel - {scenario}"
        )
        fig_weight.update_layout(margin={"r":0, "t":40, "l":0, "b":0})
        st.plotly_chart(fig_weight, key="map_weight")

# TAB 4 : méthodologie & Formules
with tab_methode:
    st.markdown("### Démarche méthodologique de calcul")
    st.markdown("Pour évaluer la sous-représentation ou la surreprésentation d'un groupe démographique, le modèle compare le volume de grands électeurs effectivement capté par ce groupe (**Actual**) à ce qu'il obtiendrait si le système distribuait le pouvoir de manière parfaitement homogène sur le territoire (**Expected**).")

    st.markdown("---")
    
    # équation 1
    st.markdown("#### 1. Nombre de grands électeurs réels (Actual)")
    st.latex(r"\text{Actual}_g = \sum_{s \in \text{États}} \left( \frac{\text{CVAP}_{g,s}}{\text{CVAP}_s} \times \text{EV}_s \right)")
    
    st.markdown("""
    * **Explication** : Pour chaque État **s**, on calcule la proportion d'habitants appartenant au groupe **g** par rapport à la population éligible totale de l'État `(CVAP_g,s / CVAP_s)`. On multiplie ensuite cette proportion par le nombre de grands électeurs de cet État `(EV_s)`. La somme sur les 50 États donne le score total du groupe.
    * **Exemple concret (Communauté hispanique en Californie)** :
        * La Californie dispose de **54 grands électeurs** (`EV_CA = 54`).
        * Si la population éligible hispanique y représente **30 %** de la population électorale locale (`CVAP_Hispanique, CA / CVAP_CA = 0.30`).
        * La contribution de la Californie au score *Actual* des Hispaniques au niveau national est de : **0,30 × 54 = 16,2 grands électeurs**.
    """)

    st.markdown("---")

    # équa 2
    st.markdown("#### 2. Représentation théorique neutre (Expected)")
    st.latex(r"\text{Expected}_g = \left( \frac{\sum_{s} \text{CVAP}_{g,s}}{\sum_{s} \text{CVAP}_s} \right) \times \text{Total EV}")

    st.markdown("""
    * **Explication** : On détermine le pourcentage que représente le groupe **g** au niveau national sur l'ensemble de la population éligible américaine, puis on applique directement ce pourcentage au total des **538 grands électeurs**.
    * **Exemple concret** :
        * Si la communauté hispanique représente **13,5 %** de l'ensemble des citoyens éligibles aux États-Unis.
        * Dans un système strictement neutre, elle devrait capter : **13,5 % × 538 = 72,63 grands électeurs**.
    """)

    st.markdown("---")

    # équa 3
    st.markdown("#### 3. Mesure des écarts et indice de désalignement")
    st.latex(r"\text{Delta}_g = \text{Actual}_g - \text{Expected}_g")
    st.latex(r"\text{Indice de Gallagher} = \sqrt{\frac{1}{2} \sum_{g} \left( \text{Actual}\%_g - \text{Expected}\%_g \right)^2}")

    st.markdown("""
    * **Delta (Écart)** : Un résultat négatif indique une sous-représentation structurelle du groupe par rapport à son poids démographique réel. Un résultat positif traduit une surreprésentation.
    * **Indice de Gallagher** : Indicateur utilisé en science politique pour mesurer la disproportionnalité globale d'un système électoral. Un indice proche de zero indique une parfaite équité de représentation.
    """)

    st.markdown("---")
    st.markdown("### Limites méthodologiques")
    st.markdown("""
    1. **Données de population éligible (CVAP)** : L'analyse s'appuie sur le nombre de citoyens en âge de voter et non sur le taux de participation effectif, qui varie selon les sous-groupes démographiques.
    2. **Hypothèse de neutralité territoriale** : Le modèle mesure le poids de représentation théorique. Dans la réalité politique, le principe du *Winner-Take-All* ajoute une couche de distorsion liée à l'orientation politique partisane des États (*Red* / *Blue* States).
    """)
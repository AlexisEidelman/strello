# -*- coding: utf-8 -*-
"""
Created on Wed Nov  2 10:14:26 2016

@author: alexis
"""
import csv
import pandas as pd


tab = pd.read_csv('saisine_07092016.csv', sep=';', encoding='utf8',
                  quoting = csv.QUOTE_NONNUMERIC, quotechar= '"',
                  parse_dates=True,
                 )

for col in tab.columns:
    try:
        tab[col] = pd.to_datetime(tab[col])
    except:
        pass


lists = ['Non traités', 'précision de la question avec le "saisisseur" - envoyé',
       'Préciser la question (1 semaine)',
       "Contacter l'administration (2 semaines)",
       'En attente / Faire une 1ère relance (20 jours)',
       'Faire une 2ème relance (2 semaines)',
       'Traitement technique à réaliser',
       "Retourner vers l'auteur (1 semaine)", 'Traités',
       'Traités  ✓ Données dispos sur data.gouv.fr',
       'Traités  ✓  Données envoyées au saisisseur',
       'Traités ✓ En attente de la diffusion sur data.gouv.fr',
       'Traités ✓ En attente de transmission au saisiseur',
       'Traités ❌ Obstacle technique', 'Traités ❌ Secret',
       'Abandon de traitement', 'Refus de traitement', 'Autres']

traites = [
       'Traités  ✓ Données dispos sur data.gouv.fr',
       'Traités  ✓  Données envoyées au saisisseur',
       'Traités ✓ En attente de la diffusion sur data.gouv.fr',
       'Traités ✓ En attente de transmission au saisiseur',
       'Traités ❌ Obstacle technique', 'Traités ❌ Secret',
       'Abandon de traitement', 'Refus de traitement']


## cleaning ###

id_to_remove = [
    '55b79d572bc64ef1b2d330f9', '55c0c5488b098d6c6c157b84',
    # on a multiplié les cartes au début
    '574f0a5aecbceb5bd3b92247', # saisine DGT a été éclatée
    '56df070273782618be6119a5', # redondant avec 56df06f84ceac9c328d3496f qui a pris le lead
    ]
# Note ça correspond aux cartes "closed = True"
tab = tab[~tab['id'].isin(id_to_remove)]

tab.loc[tab['id'] == '56b09f4578a5a5feb077af35', 'Traités ❌ Obstacle technique'] = \
    pd.to_datetime('2016-03-09T13:11:08.175Z')
#on retire les cartes là pour archivage
tab = tab[tab['list'] != 'Autres']


try: 
    assert tab[traites].notnull().sum(axis=1) <= 1
except:
    pb = tab[traites].notnull().sum(axis=1) > 1
    for row in tab[pb].iterrows():
        date_classement = row[1][traites]
        premiere_date = date_classement[date_classement.notnull()].min()
        tab.loc[row[0], traites] = pd.NaT
        tab.loc[row[0], row[1]['list']] = premiere_date
        # print(tab.loc[row[0], ['name'] + traites])
    # => ce sont souvent des hésitations quant au classement de la saisine
    # rien de grave
assert all(tab[traites].notnull().sum(axis=1) <= 1)

# au début on avait une seule colonne "traitée" que l'on a ensuite éclatée.
# la date qui apparait ensuite est donc la date de création de la colonne
# on envoit donc la date dans une autre colonne
# remarque : c'est la même moulinette qu'au dessus en incluant Traités dans la
#liste des variables. On garde ce format pour plus de lisibilité.
for row in tab[tab['Traités'].notnull()].iterrows():
    # find filled value
    assert any(row[1][traites].notnull())
    for col in traites:
        if pd.notnull(row[1][col]):
            tab.loc[row[0], col] = row[1]['Traités']
    # print(tab.loc[row[0]])


assert all(tab[traites].notnull().sum(axis=1) <= 1)
assert all(tab['created'].notnull())


# statistique: 

## traites :
fin = pd.to_datetime(tab[traites].max(axis=1))
tab['duree'] = (fin - tab.created) / pd.Timedelta('1d')
tab.sort_values('duree', ascending=False, inplace=True)
tab.set_index('created', inplace=True)

# en_cours = tab[tab['duree'].isnull()]
vraies = tab[~tab.list.isin(['Refus de traitement', 'Abandon de traitement'])]
finies = vraies[vraies['duree'].notnull()]
print( 100*finies['list'].value_counts(normalize=True))

toutes = vraies.copy()
from datetime import date
toutes['delai'] = pd.to_datetime(date.today())
toutes['delai'] -= toutes.index
toutes['delai'] /= pd.Timedelta('1D')

toutes.loc[toutes['duree'].isnull(), 'duree'] = \
    toutes.loc[toutes['duree'].isnull(), 'delai']

toutes.sort_values('duree', ascending=False, inplace=True)

toutes.resample('3M').mean()['duree'].plot()
finies.resample('3M').mean()['duree'].hist()
toutes['duree'].hist()
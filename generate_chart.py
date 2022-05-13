import os
import dash
import spacy
import plotly
import webbrowser
import pandas as pd
from dash import html
from dash import dcc
from dash.dependencies import Input, Output
from collections import Counter
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from threading import Timer

app = dash.Dash(__name__)

# ---------------------------------------------------
# Load up spaCy and designate the subfolder location.
# ---------------------------------------------------

dir_path = os.getcwd()
subfolder = dir_path + '/storage/'
nlp = spacy.load('en_core_web_sm')

files = [os.path.join(subfolder, f) 
         for f in os.listdir(subfolder)
         if os.path.isfile(os.path.join(subfolder, f))]

# ---------------------------------------------------
# Used only to automatically open a browser so the 
# user doesn't need to click the link each time the
# script is ran.
# ---------------------------------------------------
def launch_browser():
      webbrowser.open_new('http://127.0.0.1:8050/')

def get_dialogue_info(character_csv: str) -> tuple:
    '''
    Given a file name from the "storage" subfolder, return the character's
    name, their responses, and their script notes (approximately their 
    sentiments) as a mixed tuple of string and spaCy docs.

                Parameters:
                    character_csv (str):
                    The name of the file found in the "storage" subfolder.

                Returns:
                    character_name, words, nouns, verbs, adjs, sentiment_doc (tuple):
                    The character's name, their responses, and their responses
                    sorted based on the type of word.

    '''
    # ---------------------------------------------------
    # Recover character's name from filename and also
    # concatenate every response into a single string for
    # spaCy to handle.
    # ---------------------------------------------------
    character_name = ' '.join(map(lambda x: str(x).capitalize(), character_csv.split('_'))).replace('.csv', '')
    character_csv = pd.read_csv(subfolder + character_csv)
    doc = nlp(' '.join(map(lambda x: str(x).lower(), character_csv['RESPONSE TEXT'])))

    # ---------------------------------------------------
    # Use list comprehensions to get words and specific
    # types of words for ease-of-use with a plotly
    # dropdown graph.
    # ---------------------------------------------------
    words = [token.text
             for token in doc
             if not token.is_stop and not token.is_punct]

    nouns = [token.text
             for token in doc
             if (not token.is_stop and
                 not token.is_punct and
                 token.pos_ == 'NOUN')]

    verbs = [token.text
             for token in doc
             if (not token.is_stop and
                 not token.is_punct and
                 token.pos_ == 'VERB')]

    adjs = [token.text
             for token in doc
             if (not token.is_stop and
                 not token.is_punct and
                 token.pos_ == 'ADJ')]

    # ---------------------------------------------------
    # Create a sentiment doc for spaCy to handle, similar
    # to doc above. Note: Can replace `.dropna()` with
    # .fillna('neutral') like in the notebook.
    # ---------------------------------------------------
    script_notes = [str(entry).split('/')[-1].strip().lower() 
                      for entry in character_csv['SCRIPT NOTES'].dropna()]
    sentiment_doc = nlp(' '.join(map(lambda x: str(x).lower(), script_notes)))
    sentiment = [token.text
                 for token in sentiment_doc
                 if not token.is_stop and not token.is_punct]

    return character_name, words, nouns, verbs, adjs, sentiment

def make_graph(character_filename: str) -> plotly.graph_objects.Figure:
        '''
        Given a file name from the "storage" subfolder, return the character's
        dialogue summary as a Plotly figure.

                    Parameters:
                        character_csv (str):
                        The name of the file found in the "storage" subfolder.

                    Returns:
                        A plotly figure with the character's ten most common 
                        words and sentiments.

        '''
        try:
            character_dialogue = get_dialogue_info(character_filename)

            fig = make_subplots(rows=2, cols=1, subplot_titles=['{character}\'s Most Common Words'.format(character=character_dialogue[0]), 
                                                                'Most Common Sentiments'])

            final_cols = character_dialogue[1:-1]
            final_names = ['All', 'Noun', 'Verb', 'Adjective']

            # ---------------------------------------------------
            # Iterate over the dialogue columns to create a 2x1
            # subplot of most common words and frequency, as well
            # as the most common sentiments and frequency.
            # ---------------------------------------------------

            for column, column_name, color in zip(final_cols, final_names, ['#6afcb8', '#6aaefc', '#6e6afc', '#fcb86a']):
                    if column_name == 'All':
                        temp = pd.DataFrame(Counter(column).most_common(10))
                        fig.add_trace(
                            go.Bar(
                                x=pd.DataFrame(temp)[0],
                                y=pd.DataFrame(temp)[1],
                                visible=True,
                            ),
                            row=1,
                            col=1
                        )
                    else:
                        temp = pd.DataFrame(Counter(column).most_common(10))
                        fig.add_trace(
                            go.Bar(
                                x=pd.DataFrame(temp)[0],
                                y=pd.DataFrame(temp)[1],
                                visible=False,
                                marker_color=color
                            ),
                            row=1,
                            col=1
                        )
            fig.add_trace(
                go.Bar(
                    x=pd.DataFrame(Counter(character_dialogue[-1]).most_common(10))[0],
                    y=pd.DataFrame(Counter(character_dialogue[-1]).most_common(10))[1],
                ),
                row=2,
                col=1
            )

            # ---------------------------------------------------
            # Hide the legend since the dropdown menu will show 
            # what's selected anyway
            # ---------------------------------------------------
            fig.update(layout_showlegend=False)

            # Dropdown
            fig.update_layout(
                updatemenus=[
                    dict(
                        active=0,
                        buttons=list([
                            dict(label='All',
                                method='update',
                                args=[{'visible': [True, False, False, False, True]}
                                        ]),
                            dict(label='Verbs',
                                method='update',
                                args=[{'visible': [False, True, False, False, True]},
                                        ]),
                            dict(label='Nouns',
                                method='update',
                                args=[{'visible': [False, False, True, False, True]},
                                        ]),
                            dict(label='Adjectives',
                                method='update',
                                args=[{'visible': [False, False, False, True, True]},
                                        ]),
                        ])
                    )
                ]
            )

            return fig

        # ---------------------------------------------------
        # Bare minimum error handling: needs improvement.
        # ---------------------------------------------------
        except Exception as e:
            print(e)

# ---------------------------------------------------
# `options` defined here so that the passed parameter
# is sorted and the dropdown in the actual Dash app
# is in alphabetical order.
# ---------------------------------------------------
options=[{
        'label': ' '.join([p.capitalize() for p in str(i).split('/')[-1].replace('.csv', '').split('_')]),
        'value': str(i)} for i in files]

app.layout = html.Div([
    dcc.Dropdown(id='filename', options=sorted(options, key=lambda x: x['label']),
                 value=subfolder+'cait.csv'),
    dcc.Graph(id='graphs')
])

@app.callback(
    Output(component_id='graphs', component_property='figure'),
    [
        Input('filename', 'value')
    ]
)
def analysis(values):
    if values is not None:
        return make_graph(values.split('/')[-1])
    else:
        return make_graph('cait.csv')

if __name__ == '__main__':
    Timer(1, launch_browser).start()
    app.run_server(port=8050, debug=False)
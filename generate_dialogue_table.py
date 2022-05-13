import requests
import math
import sys
import pandas as pd
from bs4 import BeautifulSoup

def trim_tags(sample: str) -> str:
    '''
    Given a string, from a BeautifulSoup select query on a CSS selector,
    trim the <th>, </th>, <td>, and </td> tags along with the escaped
    new line character \\n.
    
    Parameters
    ==========
    @ sample (str): A CSS selector
    '''
    return sample.replace('<th>', '').replace('</th>', '').replace('<td>', '').replace('</td>', '').replace('\n', '')

def purge_nondialogue(entry: str) -> str:
    '''
    Given a string, from a BeautifulSoup select query on a CSS selector,
    remove the entry if there is any indication it is not dialogue.
    
    Parameters
    ==========
    @ sample (str): A CSS selector
    '''
    for idx in range(len(entry)):
        if '<td class=' in str(entry[idx]):
            entry[idx] = '*'
    return entry

def create_table(character: str = 'Cait') -> pd.core.frame.DataFrame:
    '''
    Given the name of a character from Fallout 4,
    generate a table containing all dialogue of
    the character.
    
    Parameters
    ==========
    @ character (str): The name of the character.
    '''
    url = f'https://fallout-archive.fandom.com/wiki/{character}%27s_dialogue'
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'lxml')

    # Find necessary number of children
    num_children = math.ceil(len(soup.select('table tbody td:nth-child(n)')) / len(soup.select('table tbody td:nth-child(3)')))

    columns_ = [trim_tags(str(child)) for child in soup.select('tr th:nth-child(n)')][2:]
    massive_list_ = [soup.select(f'table tbody td:nth-child({idx + 1})') for idx in range(num_children)]
    purged_massive_list = [purge_nondialogue(massive_list_[idx]) for idx in range(len(massive_list_))]
    trimmed_purge = [[trim_tags(str(entry)) for entry in purged_massive_list[idx]] for idx in range(len(purged_massive_list))]

    for idx in range(len(trimmed_purge)):
        while '*' in trimmed_purge[idx]:
            trimmed_purge[idx].remove('*')

    # Get the max length of an entry
    lens = []
    for entry in trimmed_purge:
        lens.append(len(entry))
    max_len = max(lens)

    # Adjusts shorter entries to match max length
    for entry in trimmed_purge:
        if len(entry) < max_len:
            delta = max_len - len(entry)
            for idx in range(delta):
                entry.append('')

    df = pd.DataFrame([], columns = columns_)

    for idx, cat in enumerate(df.columns):
        df[cat] = trimmed_purge[idx]

    return df

if __name__=='__main__':
    try:
        if len(sys.argv) > 1:
            character_name = str(sys.argv[1]).replace(' ', '_')
        else:
            character_name = 'Cait'

        table = create_table(character_name)
        table.to_csv(f'{character_name.lower()}_dialogue.csv', index = False)
        print('A new dialogue file has been created!')

    except:
        print('A new dialogue file could not be created. Exiting program.')
        
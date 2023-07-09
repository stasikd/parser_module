import json
import sqlite3
from nltk import word_tokenize
from process_sql import tokenize

# from test_module.process_sql import tokenize

# import nltk
# nltk.download('punkt')

from more_itertools import split_after, split_at

WHERE_OPS = ('not', 'between', '=', '>', '<', '>=', '<=', '!=', 'like', 'is', 'exists')
COND_OPS = ('and', 'or')
AGG_OPS = ('none', 'max', 'min', 'count', 'sum', 'avg')

cmp_op_idx2op_symbol = {0: '=', 1: '>', 2: '<'}
ctr_symbol2cmp_op_idx = {v: k for k, v in cmp_op_idx2op_symbol.items()}
agg_idx2op_name = {1: 'max', 2: 'min', 3: 'count', 4: 'sum', 5: 'avg'}
ctr_name2agg_idx = {v: k for k, v in agg_idx2op_name.items()}

def parse_condition(conditions):
    for tok in conditions:
        if tok in WHERE_OPS:
            agg_tok_idx = conditions.index(tok)
            agg_tok = tok
            cond_col = ' '.join(conditions[:agg_tok_idx])
            rest_cond = ' '.join(conditions[conditions.index(agg_tok)+1:])
    return [cond_col, ctr_symbol2cmp_op_idx[agg_tok], rest_cond]


def parse_query(query):
    cond_list, final_dict = [], {}

    toks = tokenize(query)
    col_to_select_with_agg = toks[1:toks.index('from')]

    isAgg = False
    isCond = False
    col_to_select_agg = list(split_after(col_to_select_with_agg, lambda x: x in AGG_OPS))
    if col_to_select_agg[0][0] in AGG_OPS:
        col_to_select = ' '.join(col_to_select_agg[1])
        col_agg = col_to_select_agg[0][0]
        isAgg = True
    else:
        col_to_select = ' '.join(col_to_select_agg[0])

    if 'where' in toks:
        isCond = True
        conditions = toks[toks.index('where') + 1:]
        for c in list(split_at(conditions, lambda x: x in COND_OPS)):
            cond_list.append(parse_condition(c))

    final_dict['sel'] = col_to_select
    final_dict['agg'] = 0 if not isAgg else ctr_name2agg_idx[col_agg]
    final_dict['conds'] = [] if not isCond else cond_list

    return final_dict


def encode_dict(origin_dict):
    encoded_dict = origin_dict.copy()
    col_names = set()

    col_names.add(origin_dict['sel'])
    for cond in origin_dict['conds']:
        col_names.add(cond[0])

    id2colname = {k: v for k, v in enumerate(col_names)}
    colname2id = {v: k for k, v in id2colname.items()}

    encoded_dict['sel'] = colname2id[origin_dict['sel']]
    for cond in origin_dict['conds']:
        cond[0] = colname2id[cond[0]]

    return encoded_dict
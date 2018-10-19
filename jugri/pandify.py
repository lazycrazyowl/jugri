from gremlin_python.structure.graph import Element, Path
from gremlin_python.process.graph_traversal import GraphTraversal
import pandas as pd
import collections
import logging

logger = logging.getLogger(__name__)


def _flatten(d, parent_key='', sep='_'):
    """
    Flatten nested fields using recursive calls.
    :param d: dictionary
    :param parent_key: current key
    :param sep: key separator
    :return: flattened dictionary
    """
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + str(k) if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(_flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def toDF(gremlin_traversal, keep_first_only=None, key_value_pairs=False, flatten_dict=True):
    # type: (bool, bool, bool) -> pd.DataFrame
    """
    Converts a Gremlin Traversal to a Pandas DataFrame. It expects a traversal or a list of traversal results.
    :param gremlin_traversal: A gremlinpython graph traversal (e.g. g.V().limit(5))
            or a list (e.g. g.V().limit(5).toList())
    :param keep_first_only: Treats every field as a singular field. Only first values are kept.
    :param key_value_pairs: Set it to True when a map is returned. The DataFrame will have only two columns: the key and
            the values.
    :param flatten_dict: Set it to True if you have nested fields in your results. The field name will automatically
            become the "." concatenated hierarchy of the names (e.g. start.date.month, end.date.year, etc.)
    :param debug_info: Set it to True if you want to print some additional debug info. DEPRECATED
    :return: Pandas DataFrame
    """
    if type(gremlin_traversal) is GraphTraversal:
        gremlin_traversal = gremlin_traversal.toList()
    if len(gremlin_traversal) == 0:
        return pd.DataFrame()

    logger.debug("Type of first element: {}".format(type(gremlin_traversal[0])))

    if type(gremlin_traversal[0]) is dict:
        if keep_first_only is None:
            keep_first_only = True
        if flatten_dict:
            gremlin_traversal = [_flatten(_, sep='.') for _ in gremlin_traversal]
        if key_value_pairs:
            df = pd.DataFrame(data={"value": [list(_.values())[0] for _ in gremlin_traversal]},
                              index=[list(_.keys())[0] for _ in gremlin_traversal])
        else:
            df = pd.DataFrame(gremlin_traversal)
    elif isinstance(gremlin_traversal[0], Element):
        if keep_first_only is None:
            keep_first_only = False
        df = pd.DataFrame([_.__dict__ for _ in gremlin_traversal])
    elif type(gremlin_traversal[0]) is Path:
        if keep_first_only is None:
            keep_first_only = False
        df = pd.DataFrame([dict(enumerate(_)) for _ in gremlin_traversal])
    else:
        if keep_first_only is None:
            keep_first_only = False
        df = pd.DataFrame(gremlin_traversal)
    if keep_first_only:
        return df.applymap(lambda x: x[0] if type(x) is list else x)
    else:
        return df
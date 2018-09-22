# utils.py

import trafaret as T

TRAFARET = T.Dict({
    T.Key('db'):
        T.Dict({
            'location': T.String(),
        }),
    T.Key('host'): T.IP,
    T.Key('port'): T.Int(),
})
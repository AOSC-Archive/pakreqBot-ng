# test_ldap.py

import sys
import ldap

from ldap.sasl import CB_AUTHNAME, CB_PASS

LDAP_SRV = 'ldaps://whoami.aosc.io'


class freeipa_login(ldap.sasl.sasl):
    def __init__(self, name, cred):
        auth_dict = {
            CB_AUTHNAME: name,
            CB_PASS: cred,
        }
        super().__init__(auth_dict, 'LOGIN')


def parse_username(dn):
    _, dn = dn.split()
    dn_list = ldap.dn.str2dn(dn, flags=ldap.DN_FORMAT_LDAPV3)
    for dn_comp in dn_list:
        if dn_comp[0][0] == 'uid':
            return dn_comp[0][1]


if __name__ == '__main__':
    aosc_sso = ldap.initialize(LDAP_SRV, trace_level=1)
    dn = None
    try:
        # request correct password for the test account from developers
        aosc_sso.sasl_interactive_bind_s('', freeipa_login('aosc', ''))
        dn = aosc_sso.whoami_s()
    except ldap.LDAPError:
        print('Auth error')
    if not dn:
        sys.exit(1)
    print('Authenticated user: {}'.format(parse_username(dn)))

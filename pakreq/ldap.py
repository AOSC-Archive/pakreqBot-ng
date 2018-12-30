import logging
import ldap

from ldap.sasl import CB_AUTHNAME, CB_PASS

LDAP_SRV = None
LDAP_AVAILABLE = False


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


class PakreqLDAP(object):
    def __init__(self, url):
        self.ldap_avail = False
        if not url:
            logging.warning('LDAP authentication disabled, no URL')
            return
        test_conn = ldap.initialize(url)
        try:
            test_conn.start_tls_s()
            self.ldap_avail = True
        except ldap.OPERATIONS_ERROR:
            self.ldap_avail = True
            # TLS already established, will throw OP_ERR
        except Exception:
            logging.warning('LDAP authentication disabled, invalid config')

        if self.ldap_avail:
            self.ldap_url = url
            logging.info('LDAP authentication enabled.')

    def ldap_login(self, user, pwd):
        if not self.ldap_avail:
            return False
        aosc_sso = ldap.initialize(self.ldap_url)
        try:
            aosc_sso.start_tls_s()
        except Exception:
            pass
        dn = None
        try:
            aosc_sso.sasl_interactive_bind_s('', freeipa_login(user, pwd))
            dn = aosc_sso.whoami_s()
            aosc_sso.unbind()
        except Exception:
            return False
        if not dn:
            return False
        return True

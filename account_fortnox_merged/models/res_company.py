# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution, third party addon
#    Copyright (C) 2004-2020 Vertel AB (<http://vertel.se>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import json
import logging
import base64
_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    invoice_fortnox = fields.Boolean(string="Send to Fortnox", default=True)


class res_company(models.Model):
    _inherit = ['res.company', 'mail.thread', 'mail.activity.mixin']
    _name = 'res.company'

    fortnox_authorization_code = fields.Char(string='Authorization code', help="You get this code from your FortNox Account when you activate Odoo", store=True)
    fortnox_client_secret = fields.Char(string='Client Secret', help="You get this code from your Odoo representative", store=True)
    fortnox_access_token = fields.Text(string='Access Token', help="With autorization code and client secret you generate this code ones", store=True)
    fortnox_client_id = fields.Char(string='Client ID', help="The public ID of the integration", store=True)
    fortnox_token_expiration = fields.Char(store=True)
    fortnox_refresh_token = fields.Text(store=True)

    def fortnox_get_access_token_new(self):
        if not self.fortnox_access_token:
            if not self.fortnox_authorization_code:
                raise UserError("You have to set up Authorization_token for FortNox, you get that when you activate Odoo in your FortNox-account")
            if not self.fortnox_client_secret:
                raise UserError("You have to set up Client_secret for FortNox, you get that when you activate Odoo in your FortNox-account")
            if not self.fortnox_client_id:
                raise UserError("You have to supply the client ID of the integration")
            try:
                credentials_encoded = f"{self.fortnox_client_id}:{self.fortnox_client_secret}".encode("utf-8")
                credentials_b64encoded = base64.b64encode(credentials_encoded).decode("utf-8")
                r = requests.post(
                    url="https://apps.fortnox.se/oauth-v1/token",
                    headers = {
                        "Content-Type": "application/x-www-form-urlencoded",
                        "Authorization": f"Basic {credentials_b64encoded}",
                    },
                    data = {
                        'grant_type': 'authorization_code',
                        'code': self.fortnox_authorization_code,
                        'redirect_uri': 'https://vertel.se'
                    }
                )
                if r.status_code not in (200, 201, 204):
                    raise UserError(f'FortNox: StatusCode:{r.status_code}, \n'
                                    f'Content:{r.content}')
                auth_rec = json.loads(r.content)
                self.fortnox_access_token = auth_rec.get('access_token')
                self.fortnox_refresh_token = auth_rec.get('refresh_token')
                self.fortnox_token_expiration = time.time() + auth_rec.get('expires_in')
            except requests.exceptions.RequestException as e:
                raise UserError('HTTP Request failed %s' % e)
        else:
            if self.fortnox_token_expiration and time.time() >= self.fortnox_token_expiration:
                # Access token has expired, refresh using the refresh token
                if not self.fortnox_refresh_token:
                    raise UserError('Refresh token is missing')
                try:
                    credentials_encoded = f"{self.fortnox_client_id}:{self.fortnox_client_secret}".encode("utf-8")
                    credentials_b64encoded = base64.b64encode(credentials_encoded).decode("utf-8")
                    r = requests.post(
                        url="https://apps.fortnox.se/oauth-v1/token",
                        headers = {
                            "Content-Type": "application/x-www-form-urlencoded",
                            "Authorization": f"Basic {credentials_b64encoded}",
                        },
                        data = {
                            'grant_type': 'refresh_token',
                            'refresh_token': self.fortnox_refresh_token,
                        }
                    )
                    if r.status_code not in (200, 201, 204):
                        raise UserError(f'FortNox: StatusCode:{r.status_code}, \n'
                                        f'Content:{r.content}')
                    auth_rec = json.loads(r.content)
                    self.fortnox_access_token = auth_rec.get('access_token')
                    self.fortnox_refresh_token = auth_rec.get('refresh_token')
                    self.fortnox_token_expiration = time.time() + auth_rec.get('expires_in')
                except requests.exceptions.RequestException as e:
                    raise UserError('HTTP Request failed %s' % e)
        return

    def fortnox_get_access_token(self):
        if not self.fortnox_access_token:
            if not self.fortnox_authorization_code:
                raise UserError("You have to set up Authorization_token for FortNox, you get that when you activate Odoo in your FortNox-account")
            if not self.fortnox_client_secret:
                raise UserError("You have to set up Client_secret for FortNox, you get that when you activate Odoo in your FortNox-account")
            if not self.fortnox_client_id:
                raise UserError("You have to supply the client ID of the integration")
            try:
                credentials_encoded = f"{self.fortnox_client_id}:{self.fortnox_client_secret}".encode("utf-8")
                credentials_b64encoded = base64.b64encode(credentials_encoded).decode("utf-8")
                r = requests.post(
                    url="https://apps.fortnox.se/oauth-v1/token",
                    headers = {
                       # "ClientId": self.fortnox_client_id,
                       # "ClientSecret": self.fortnox_client_secret,
                        "Content-Type": "application/x-www-form-urlencoded",
                       # "Accept": "application/json",
                        "Authorization": f"Basic {credentials_b64encoded}", 
                    },
                    data = {
                       'grant_type': 'authorization_code',
                       'code': self.fortnox_authorization_code,
                       'redirect_uri': 'https://vertel.se'
                    }
                )
                
                if r.status_code not in (200, 201, 204):
                    raise UserError(f'FortNox: StatusCode:{r.status_code}, \n'
                                    f'Content:{r.content}')
                auth_rec = json.loads(r.content)
                _logger.warning(f"{auth_rec=}")
                # _logger.warning(f"{auth_rec.get('access_token')=}")
                self.fortnox_access_token = auth_rec.get('access_token')
                self.fortnox_refresh_token = auth_rec.get('refresh_token')
                # _logger.warning(f"{self.fortnox_access_token=}")
                # msg = _("New Access Token {token}").format(self.fortnox_access_token)
                    
                # self.message_post(
                #     body=msg, subject=None, message_type='notification')
            except requests.exceptions.RequestException as e:
                raise UserError('HTTP Request failed %s' % e)
        else:
            raise UserError('Access Token already fetched')
            
    def fortnox_refresh_access_token_cron(self):
        company = self.env.user.company_id
        try:
            credentials_encoded = f"{company.fortnox_client_id}:{company.fortnox_client_secret}".encode("utf-8")
            credentials_b64encoded = base64.b64encode(credentials_encoded).decode("utf-8")
            r = requests.post(
                url="https://apps.fortnox.se/oauth-v1/token",
                headers = {
                   # "ClientId": self.fortnox_client_id,
                   # "ClientSecret": self.fortnox_client_secret,
                    "Content-Type": "application/x-www-form-urlencoded",
                   # "Accept": "application/json",
                    "Authorization": f"Basic {credentials_b64encoded}", 
                },
                data = {
                   'grant_type': 'refresh_token',
                   'refresh_token': company.fortnox_refresh_token,
                }
            )
            
#            _logger.warning(f"{credentials_b64encoded=} {self.fortnox_refresh_token=}")
            
            if r.status_code not in (200, 201, 204):
                raise UserError(f'FortNox: StatusCode:{r.status_code}, \n'
                                f'Content:{r.content}')
            auth_rec = json.loads(r.content)
            _logger.warning(f"{auth_rec=}")
            
            
            for company in self.env.user.company_ids:
                company.fortnox_access_token = auth_rec.get('access_token')
                company.fortnox_refresh_token = auth_rec.get('refresh_token')
            # msg = _("New Access Token {token}").format(self.fortnox_access_token)
                
            # self.message_post(
            #     body=msg, subject=None, message_type='notification')
        except requests.exceptions.RequestException as e:
            raise UserError('HTTP Request failed %s' % e)

    def fortnox_request(self, request_type, url, data=None, raise_error=True):
        # Customer (POST https://api.fortnox.se/3/customers)
        headers = {
            #"Access-Token": self.fortnox_access_token,
            #"Client-Secret": self.fortnox_client_secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.fortnox_access_token}"
        }
        #_logger.warning(f"{self.fortnox_access_token=}")
        _logger.info(f'FortNox: '
                     f'Request_Type:{request_type}, '
                     f'URL:{url}, '
                     f'Data:{data}')
        try:
            if request_type == 'post':
                r = requests.post(
                    url=url, headers=headers, data=json.dumps(data))
            if request_type == 'put':
                r = requests.put(
                    url=url, headers=headers, data=json.dumps(data))
            if request_type == 'get':
                r = requests.get(url=url, headers=headers)
            if request_type == 'delete':
                r = requests.delete(url=url, headers=headers)

            _logger.info(f'FortNox: return-record {r.status_code} {r.content}')
            if raise_error and r.status_code not in [200, 201, 204]:
                raise UserError(r.content)
        except requests.exceptions.RequestException as e:
            _logger.warn('FortNox: HTTP Request failed %s' % e)
            raise UserError('HTTP Request failed %s' % e)

        return r.content


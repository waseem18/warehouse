# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import wtforms
import wtforms.fields.html5

from warehouse import forms, recaptcha


class CredentialsMixin:
    username = wtforms.StringField(
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.Length(max=50),
        ],
    )

    password = wtforms.PasswordField(
        validators=[
            wtforms.validators.DataRequired(),
        ],
    )

    def __init__(self, *args, user_service, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_service = user_service


class RegistrationForm(CredentialsMixin, forms.Form):
    password_confirm = wtforms.PasswordField(
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.EqualTo(
                "password", "Passwords must match."
            ),
        ],
    )

    full_name = wtforms.StringField()

    email = wtforms.fields.html5.EmailField(
        validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.Email(),
        ],
    )

    g_recaptcha_response = wtforms.StringField()

    def __init__(self, *args, recaptcha_service, **kwargs):
        super().__init__(*args, **kwargs)
        self.recaptcha_service = recaptcha_service

    def validate_username(self, field):
        if self.user_service.find_userid(field.data) is not None:
            raise wtforms.validators.ValidationError(
                "Username exists.")

    def validate_email(self, field):
        if self.user_service.find_by_email(field.data) is not None:
            raise wtforms.validators.ValidationError("Email exists.")

    def validate_g_recaptcha_response(self, field):
        # do required data validation here due to enabled flag being required
        if self.recaptcha_service.enabled and len(field.data) <= 0:
            raise wtforms.validators.ValidationError("This field is required.")

        try:
            self.recaptcha_service.verify_response(field.data)
        except recaptcha.RecaptchaError:
            # TODO: log error
            # don't want to provide the user with any detail
            raise wtforms.validators.ValidationError("Recaptcha error.")


class LoginForm(CredentialsMixin, forms.Form):
    def validate_username(self, field):
        userid = self.user_service.find_userid(field.data)

        if userid is None:
            raise wtforms.validators.ValidationError("Invalid user.")

    def validate_password(self, field):
        userid = self.user_service.find_userid(self.username.data)
        if userid is not None:
            if not self.user_service.check_password(userid, field.data):
                raise wtforms.validators.ValidationError("Invalid password.")

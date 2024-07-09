import vobject
import datetime as dt
from django.apps import apps
from djangoyearlessdate.helpers import YearlessDate

# todo: parse groups, pref
# todo: parse unrecognized content to BaseContentLine

CELL = 'c'
WORK = 'w'
HOME = 'h'
VOICE = 'v'
TEXT = 't'
FAX = 'f'
PAGER = 'p'
OTHER = 'o'
WH_TYPE_CHOICES = {
    WORK: 'Work',
    HOME: 'Home',
    OTHER: 'Other'
}
PHONE_TYPE_CHOICES = {
    CELL: 'Cell',
    WORK: 'Work',
    HOME: 'Home',
    VOICE: 'Voice',
    TEXT: 'Text',
    FAX: 'Fax',
    PAGER: 'Pager',
    OTHER: 'Other'
}

INDIVIDUAL_KIND = 'i'
GROUP_KIND = 'g'
ORG_KIND = 'o'
LOCATION_KIND = 'l'
KIND_CHOICES = {
    INDIVIDUAL_KIND: 'Individual',
    GROUP_KIND: 'Group',
    ORG_KIND: 'Organization',
    LOCATION_KIND: 'Location'
}

MALE_GENDER = 'm'
FEMAIL_GENDER = 'f'
OTHER_GENDER = 'o'
NONE_GENDER = 'n'
UNKNOWN_GENDER = 'u'
GENDER_TYPE_CHOICES = {
    MALE_GENDER: 'Male',
    FEMAIL_GENDER: 'Female',
    OTHER_GENDER: 'Other',
    NONE_GENDER: 'Not Applicable',
    UNKNOWN_GENDER: 'Unknown'
}

TITLE = 't'
ROLE = 'r'
ORG = 'o'
ORG_PROPERTIES = {
    TITLE: 'TITLE',
    ROLE: 'ROLE',
    ORG: 'ORG',
}

X_APPLE_OMIT_YEAR = '1604'


def generate_vcard_date(yearless_bday, year) -> str:
    y_repr = str(year) if year is not None else X_APPLE_OMIT_YEAR
    mmdd = f'{yearless_bday.month:02}{yearless_bday.day:02}'
    return f'{y_repr}{mmdd}'


def generate_gender(sex, gender) -> str:
    return f'{sex if sex!="" else ""}{";" + gender if gender!="" else ""}'


def vcf_to_model_dicts(vcf: str) -> list[dict[str, list]]:
    try:
        v_iter = vobject.readComponents(vcf)
    except Exception as e:
        raise e

    vcard_model_list = []
    for v in v_iter:
        v: vobject.base.Component
        try:
            vcard_model_list.append(component_to_model_dict(v))
        except Exception as e:
            raise e

    return vcard_model_list


def get_first_or_default(contents: dict, value: str, default=''):
    return contents.get(value)[0].value if contents.get(value) is not None else default


def get_all_or_default(contents: dict, value: str, sep: str = '\n', default: str = '') -> str:
    r = None
    if contents is not None and contents.get(value):
        r = sep.join([v.value for v in contents.get(value)])
    return r if r is not None else default


def component_to_model_dict(v: vobject.base.Component) -> dict[str, list]:
    assert v.name == 'VCARD'
    contents = v.contents

    kind = get_first_or_default(contents, 'kind', INDIVIDUAL_KIND)

    # todo: parse fn for non individual kind
    names = contents.get('n')
    if len(names) > 0:
        if len(names) == 1:
            n: vobject.vcard.Name = names[0].value
        else:
            # look for pref param
            found_pref = False
            for name in names:
                if 'TYPE' in name.params and not found_pref:
                    if 'pref' in [s.lower() for s in name.params['TYPE']]:
                        # stop parse this one
                        n: vobject.vcard.Name = name.value
                        found_pref = True
            if not found_pref:
                # parse first name
                n: vobject.vcard.Name = names[0].value
        prefix = n.prefix
        first_name = n.given
        middle_name = n.additional
        last_name = n.family
        suffix = n.suffix
    else:
        # todo: parse fn better
        prefix = ''
        first_name = ''
        middle_name = ''
        last_name = contents.get('fn')[0].value
        suffix = ''

    nickname = get_first_or_default(contents, 'nickname')
    # photo =  # todo: photo...

    byear, bmonth, bday = parse_vcard_date(contents.get('bday'))
    birthday = None
    birthday_year = None
    if bday is not None and bmonth is not None:
        birthday = YearlessDate(day=bday, month=bmonth)
    if byear is not None:
        birthday_year = byear

    ayear, amonth, aday = parse_vcard_date(contents.get('anniversary'))
    anniversary = None
    anniversary_year = None
    if aday is not None and amonth is not None:
        anniversary = YearlessDate(day=aday, month=amonth)
    if ayear is not None:
        anniversary_year = ayear


    # gender = ...  # todo: gender

    note = get_all_or_default(contents, 'note')

    adr_models = parse_vcard_adr(contents.get('adr'))
    phone_models = parse_vcard_tel(contents.get('tel'))
    email_models = parse_vcard_email(contents.get('email'))
    title_models = parse_vcard_org_properties(contents.get('title'), 't')
    role_models = parse_vcard_org_properties(contents.get('role'), 'r')
    org_models = parse_vcard_org_properties(contents.get('org'), 'o')
    tag_models = parse_vcard_tag(contents.get('categories'))
    url_models = parse_vcard_url(contents.get('url'))
    url_models += parse_vcard_url(contents.get('x-socialprofile'))

    card_model = apps.get_model('account.Card')
    card = card_model(
        kind=kind,
        prefix=prefix,
        first_name=first_name,
        middle_name=middle_name,
        last_name=last_name,
        suffix=suffix,
        nickname=nickname,
        # photo=photo,
        birthday=birthday,
        birthday_year=birthday_year,
        anniversary=anniversary,
        anniversary_year=anniversary_year,
        sex='',  # sex,
        gender='',  # gender,
        note=note
    )

    return {
        'card': card,
        'adr_models': adr_models,
        'phone_models': phone_models,
        'email_models': email_models,
        'title_models': title_models,
        'role_models': role_models,
        'org_models': org_models,
        'tag_models': tag_models,
        'url_models': url_models
    }


def save_model_dict_to_db(user, model_dicts: dict, commit=True):
    for mod_dict in model_dicts:
        try:
            print(mod_dict['card'])
            new_card = mod_dict['card']
            new_card.user = user
            new_card.save()

            for mod_name, mod_list in mod_dict.items():
                if mod_name.endswith('_models'):
                    mod_name = mod_name[:-7]
                    for mod in mod_list:
                        mod.card = new_card
                        mod.save()
        except Exception as e:
            raise e


def parse_vcard_date(content_list: list | None) -> tuple[int | None, int | None, int | None]:
    # todo: regex this shit
    year = None
    month = None
    day = None
    if content_list is not None:
        try:
            d_content = content_list[0]  # parsing 1st only
            d = d_content.value

            ommit_year = 'X_APPLE_OMIT_YEAR' in d_content.params

            delim_str = ''
            if '-' in d:
                delim_str = '-'
            elif '/' in d:
                delim_str = '/'
            delimited = delim_str != ''
            delim_count = 0
            if delimited: delim_count = d.count(delim_str)

            if delimited:
                is_numeric = ''.join(d.split(delim_str)).isnumeric()
            else:
                is_numeric = d.isnumeric()

            if is_numeric:
                if delim_count == 0:
                    if len(d) in [6, 8]:
                        # YYYYMMDD or YYMMDD
                        # assume 1st 2 or 4 digits are year
                        if len(d) == 6:
                            year = int(d[:2])
                            if year <= dt.datetime.today().year % 100:  # 2000s
                                year += (dt.datetime.today().year // 100) * 100
                            else:
                                year += (dt.datetime.today().year // 100 - 1) * 100
                        month = int(d[4:6])
                        day = int(d[6:])
                    elif len(d) == 4:
                        # YYYY
                        year = int(d)
                elif delim_count == 1:
                    if d.find(delim_str) == 4:
                        # YYYY-MM format
                        year = int(d[:4])
                        month = int(d[4:6])
                    elif d.find(delim_str) == 2:
                        # MM-YYYY
                        year = int(d[2:6])
                        month = int(d[:2])
                elif delim_count == 2:
                    if len(d) == 10 and d.find(delim_str) == 4 and d.find(delim_str, 5) == 7:
                        # YYYY-MM-DD
                        ymd = d.split(delim_str)
                        year = int(ymd[0])
                        month = int(ymd[1])
                        day = int(ymd[2])
                    elif len(d) == 6 and d.find('-') == 0 and d.find('-', 1) == 1:
                        # --MMDD
                        month = int(d[2:4])
                        day = int(d[4:6])
        except:
            pass

        if ommit_year: year = None
    return year, month, day


def parse_type(content: vobject.base.ContentLine, type_choices: dict) -> str:
    found_type = ''
    if 'TYPE' in [s for s in content.params.keys()]:
        # todo: parse when TYPE not upper
        found_usable_type = False
        usable_types = [s.lower() for s in type_choices.values()]
        # todo: should parse all recognized types
        for t in content.params['TYPE']:
            if t.lower() in usable_types and not found_usable_type:
                found_usable_type = True
                return t.lower()[0]  # first letter corresponds to db value
    return found_type


def parse_vcard_adr(content_list: list | None) -> list:
    adr_list = []
    if content_list is not None:
        address_model = apps.get_model('account.Address')
        for content in content_list:
            content: vobject.base.ContentLine
            # type params
            adr_type = parse_type(content, WH_TYPE_CHOICES)
            adr: vobject.vcard.Address = content.value
            # ignore street2 possibility and only use street1
            street1 = adr.street
            city = adr.city
            state = adr.region
            zip = adr.code
            country = adr.country
            adr_list.append(
                address_model(address_type=adr_type,
                              street1=street1,
                              street2='',
                              city=city,
                              state=state,
                              zip=zip,
                              country=country)
            )
    return adr_list


def parse_vcard_tel(content_list: list | None) -> list:
    tel_list = []
    if content_list is not None:
        phone_model = apps.get_model('account.Phone')
        for content in content_list:
            content: vobject.base.ContentLine
            # type params
            phone_type = parse_type(content, PHONE_TYPE_CHOICES)
            phone_number = content.value  # todo: gotta format / validate this
            tel_list.append(
                phone_model(phone_number=phone_number,
                            phone_type=phone_type)
            )
    return tel_list


def parse_vcard_email(content_list: list | None) -> list:
    email_list = []
    if content_list is not None:
        email_model = apps.get_model('account.Email')
        for content in content_list:
            content: vobject.base.ContentLine
            # type params
            email_type = parse_type(content, WH_TYPE_CHOICES)
            email_address = content.value
            email_list.append(
                email_model(email_type=email_type,
                            email_address=email_address)
            )
    return email_list


def parse_vcard_org_properties(content_list: list | None, prop_type: str) -> list:
    assert prop_type in ORG_PROPERTIES.keys()
    prop_list = []
    if content_list is not None:
        base_org_model = apps.get_model('account.BaseOrgProperty')
        for content in content_list:
            content: vobject.base.ContentLine
            # type params - not saved in db
            # email_type = parse_type(content, WH_TYPE_CHOICES)
            prop_val = content.value
            if isinstance(prop_val, list):  # eg org with ; delimiter
                prop_val = ', '.join(prop_val)
            prop_list.append(
                base_org_model(prop_type=prop_type,
                               value=prop_val)
            )
    return prop_list


def parse_vcard_tag(content_list: list | None) -> list:
    tag_str_list = []
    tag_model_list = []
    if content_list is not None:
        tag_model = apps.get_model('account.Tag')
        for content in content_list:
            content: vobject.base.ContentLine
            tag_value = content.value
            if isinstance(tag_value, list):
                for t in tag_value:
                    tag_str_list.append(t)
            else:
                tag_str_list.append(tag_value)
        for t in tag_str_list:
            tag_model_list.append(
                tag_model(tag=t)
            )
    return tag_model_list


def parse_vcard_url(content_list: list | None) -> list:
    url_list = []
    if content_list is not None:
        url_model = apps.get_model('account.Url')
        for content in content_list:
            content: vobject.base.ContentLine
            #  recognized type param
            url_type = parse_type(content, WH_TYPE_CHOICES)

            # use first unrecognized type param as optional label
            label = ''
            if 'TYPE' in [s for s in content.params.keys()]:
                # todo: parse when TYPE not upper
                found_unusable_type = False
                usable_types = [s.lower() for s in WH_TYPE_CHOICES.values()]
                for t in content.params['TYPE']:
                    if t.lower() not in usable_types and not found_unusable_type:
                        found_unusable_type = True
                        label = t

            url = content.value
            url_list.append(
                url_model(url_type=url_type, url=url, label=label)
            )
    return url_list

import os.path


PROFILE_PHOTO_DIR = os.path.join('users', 'profile', 'photo')
VCARD_DIR = os.path.join('users', 'vcard')

CONTENT_TYPES = (
    'email',
    'phone',
    'address',
    'link',
)

CONTENT_CATEGORIES = {
    'Contact Info': [
        'Email',
        'Phone',
        'Address',
    ],
    'Link': [
        'Website',
        'GitHub'
    ],
}

import os.path
from abc import ABC
from dataclasses import dataclass


PROFILE_PHOTO_DIR = os.path.join('users', 'profile', 'photo')
ATTACHMENT_MODEL_DIR = os.path.join('users', 'models', 'attachment')

CONTENT_TYPES = (
    'email',
    'phone',
    'address',
    'link',
    'attachment',
    'award',
    'certificate',
    'license',
    'membership',
    'workexperience',
    'volunteerwork',
    'education',
    'project',
    'publishedwork',
    'patent',
)

CONTENT_CATEGORIES = {
    'Contact Info': [
        'Email',
        'Phone',
        'Address',
    ],
    'Link': [
        'Website',
        'GitHub',
    ],
    'Attachment': [
        'Document',
        'Image',
    ],
    'Professional': [
        'Work Experience',
        'Project',
        'Membership',
        'License',
        'Certificate',
    ],
    'Educational': [
        'Education',
    ],
    'Achievements': [
        'Published Work',
        'Award',
        'Patent',
    ],
    'Interests': [
        'Volunteer Work',
    ],
}


class ContentCategories:
    categories = [
        'ContactInfo',
        'Link',
        'Attachment',
        'Professional',
        'Educational',
        'Achievements',
        'Interests',
    ]

    @dataclass
    class Category:
        display_name: str
        is_app: bool
        contents: dict

        @property
        def name(self):
            return ''.join(d.lower() for d in self.display_name.split())

        def __iter__(self):
            return iter(self.contents)

        def __len__(self):
            return len(self.contents)

    def __iter__(self):
        return (getattr(self, c) for c in self.categories)

    ContactInfo = Category(
        display_name='Contact Info',
        is_app=False,
        contents={
            'Email': None,
            'Phone': None,
            'Address': None,
        },
    )

    Link = Category(
        display_name='Link',
        is_app=True,
        contents={
            'Website': 1,
            'GitHub': 2,
        }
    )

    Attachment = Category(
        display_name='Attachment',
        is_app=True,
        contents={
            'Document': 'D',
            'Image': 'I',
        }
    )

    Professional = Category(
        display_name='Professional',
        is_app=False,
        contents={
            'Work Experience': None,
            'Project': None,
            'Membership': None,
            'License': None,
            'Certificate': None,
        }
    )

    Educational = Category(
        display_name='Educational',
        is_app=False,
        contents={
            'Education': None,
        }
    )

    Achievements = Category(
        display_name='Achievements',
        is_app=False,
        contents={
            'Published Work': None,
            'Award': None,
            'Patent': None,
        }
    )

    Interests = Category(
        display_name='Interests',
        is_app=False,
        contents={
            'Volunteer Work': None,
        }
    )

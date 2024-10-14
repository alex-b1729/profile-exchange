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
        'Project',
        'Membership',
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
        contents: list

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
        contents=[
            'Email',
            'Phone',
            'Address',
        ],
    )

    Link = Category(
        display_name='Link',
        is_app=True,
        contents=[
            'Website',
            'GitHub',
        ]
    )

    Attachment = Category(
        display_name='Attachment',
        is_app=True,
        contents=[
            'Document',
            'Image',
        ]
    )

    Professional = Category(
        display_name='Professional',
        is_app=False,
        contents=[
            'Work Experience',
            'Project',
            'Membership',
            'License',
            'Certificate',
        ]
    )

    Educational = Category(
        display_name='Educational',
        is_app=False,
        contents=[
            'Education',
        ]
    )

    Achievements = Category(
        display_name='Achievements',
        is_app=False,
        contents=[
            'Published Work',
            'Award',
            'Patent',
        ]
    )

    Interests = Category(
        display_name='Interests',
        is_app=False,
        contents=[
            'Volunteer Work',
        ]
    )

if __name__ == '__main__':
    cc = ContentCategories()
    for category in cc:
        print(category)
        for c in category:
            print(c)

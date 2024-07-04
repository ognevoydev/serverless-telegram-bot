from .contact import contact
from .demo import demo
from .help import help
from .my_files import my_files, back_to_list
from .not_ready import not_ready
from .sign_up import sign_up
from .upload import upload

all_handlers = [
    sign_up,
    upload,
    my_files,
    not_ready,
    back_to_list,
    help,
    contact,
    demo
]

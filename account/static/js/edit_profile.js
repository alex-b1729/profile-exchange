let addPhoneButton = document.querySelector("#add-phone-form");
addPhoneButton.addEventListener('click', addForm);
addPhoneButton.content = 'phone';

let addEmailButton = document.querySelector("#add-email-form");
addEmailButton.addEventListener('click', addForm);
addEmailButton.content = 'email';

let addUrlButton = document.querySelector("#add-url-form");
addUrlButton.addEventListener('click', addForm);
addUrlButton.content = 'url';

let addAddressButton = document.querySelector("#add-address-form");
addAddressButton.addEventListener('click', addForm);
addAddressButton.content = 'address';

let addOrgButton = document.querySelector("#add-org-form");
addOrgButton.addEventListener('click', addForm);
addOrgButton.content = 'org';
// todo: doesn't work for org, maybe logo?
// todo: how do I reset the logo once that's working?

let addTagButton = document.querySelector("#add-tag-form");
addTagButton.addEventListener('click', addForm);
addTagButton.content = 'tag';

function addForm(e) {
    e.preventDefault();
    let content = e.currentTarget.content;

    let container = document.querySelector(`#${content}-form-container`);
    let form = document.querySelectorAll(`.${content}-form`);
    let addButton = document.querySelector(`#add-${content}-form`);
    let totalForms = document.querySelector(`#id_${content}-TOTAL_FORMS`);

    let formNum = form.length - 1;

    let newForm = form[0].cloneNode(true);
    let formRegex = RegExp(`${content}-(\\d){1}-`, 'g');

    formNum++;
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `${content}-${formNum}-`);

    let inputs = newForm.querySelectorAll('input');
    inputs.forEach(input => {
        // todo: doesn't set choices correctly
        if (input.hasAttribute('value')) {
            if (content === 'phone') {
                input.setAttribute('value', 'Cell');
            } else if (content === 'address'){
                input.setAttribute('value', 'Work');
            } else {
                input.setAttribute('value', '');
            }
        }
        if (input.type === 'checkbox' || input.type === 'radio') {
            input.checked = false;
        }
    });

    container.insertBefore(newForm, addButton);
    totalForms.setAttribute('value', `${formNum + 1}`);
}

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

let addTitleButton = document.querySelector("#add-title-form");
addTitleButton.addEventListener('click', addForm);
addTitleButton.content = 'title';

let addOrgButton = document.querySelector("#add-org-form");
addOrgButton.addEventListener('click', addForm);
addOrgButton.content = 'org';

let addRoleButton = document.querySelector("#add-role-form");
addRoleButton.addEventListener('click', addForm);
addRoleButton.content = 'role';

let addTagButton = document.querySelector("#add-tag-form");
addTagButton.addEventListener('click', addForm);
addTagButton.content = 'tag';

function addForm(e) {
    e.preventDefault();
    let content = e.currentTarget.content;

    let container = document.querySelector(`#${content}-form-container`);
    let form = document.querySelectorAll(`.${content}-form`);
    let addButton = document.querySelector(`#add-${content}-form`);
    let totalForms = document.querySelector(`#id_${content}_set-TOTAL_FORMS`);

    let formNum = form.length - 1;

    let newForm = form[form.length-1].cloneNode(true);
    let formRegex = RegExp(`${content}_set-(\\d){1}-`, 'g');

    formNum++;
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `${content}_set-${formNum}-`);

//    container.insertBefore(newForm, addButton);
    container.appendChild(newForm);
    totalForms.setAttribute('value', `${formNum + 1}`);
}

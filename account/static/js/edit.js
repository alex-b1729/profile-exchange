let container = document.querySelector("#form-container")

let emailForm = document.querySelectorAll(".email-form")
let addEmailButton = document.querySelector("#add-email-form")
let totalEmailForms = document.querySelector("#id_email_addresses-TOTAL_FORMS")

let emailFormNum = emailForm.length - 1

addEmailButton.addEventListener('click', addEmailForm)

function addEmailForm(e) {
    e.preventDefault()

    let newForm = emailForm[0].cloneNode(true)
    let formRegex = RegExp(`email_addresses-(\\d){1}-`, 'g')

    emailFormNum++
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `email_addresses-${emailFormNum}-`)

    newForm.querySelector(`#id_email_addresses-${emailFormNum}-email_address`).setAttribute('value', '')
    newForm.querySelector(`#id_email_addresses-${emailFormNum}-is_primary`).checked = false
    newForm.querySelector(`#id_email_addresses-${emailFormNum}-DELETE`).checked = false

    container.insertBefore(newForm, addEmailButton)

    totalEmailForms.setAttribute('value', `${emailFormNum+1}`)
}
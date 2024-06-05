let container = document.querySelector("#form-container")

let emailForm = document.querySelectorAll(".email-form")
let addEmailButton = document.querySelector("#add-email-form")
let totalEmailForms = document.querySelector("#id_email_addresses-TOTAL_FORMS")

let phoneForm = document.querySelectorAll(".phone-form")
let addPhoneButton = document.querySelector("#add-phone-form")
let totalPhoneForms = document.querySelector("#id_phone_numbers-TOTAL_FORMS")

let addressForm = document.querySelectorAll(".address-form")
let addAddressButton = document.querySelector("#add-address-form")
let totalAddressForms = document.querySelector("#id_postal_addresses-TOTAL_FORMS")

let emailFormNum = emailForm.length - 1
let phoneFormNum = phoneForm.length - 1
let addressFormNum = addressForm.length - 1

addEmailButton.addEventListener('click', addEmailForm)
addPhoneButton.addEventListener('click', addPhoneForm)
addAddressButton.addEventListener('click', addAddressForm)

// these functions should be combined
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

function addPhoneForm(e) {
    e.preventDefault()

    let newForm = phoneForm[0].cloneNode(true)
    let formRegex = RegExp(`phone_numbers-(\\d){1}-`, 'g')

    phoneFormNum++
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `phone_numbers-${phoneFormNum}-`)

    newForm.querySelector(`#id_phone_numbers-${phoneFormNum}-phone_number`).setAttribute('value', '')
    newForm.querySelector(`#id_phone_numbers-${phoneFormNum}-phone_type`).value = 'mobile'
    newForm.querySelector(`#id_phone_numbers-${phoneFormNum}-DELETE`).checked = false

    container.insertBefore(newForm, addPhoneButton)

    totalPhoneForms.setAttribute('value', `${phoneFormNum+1}`)
}

function addAddressForm(e) {
    e.preventDefault()

    let newForm = addressForm[0].cloneNode(true)
    let formRegex = RegExp(`postal_addresses-(\\d){1}-`, 'g')

    addressFormNum++
    newForm.innerHTML = newForm.innerHTML.replace(formRegex, `postal_addresses-${addressFormNum}-`)
    
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-street1`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-street2`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-city`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-state`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-zip`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-country`).setAttribute('value', '')
    newForm.querySelector(`#id_postal_addresses-${addressFormNum}-DELETE`).checked = false

    container.insertBefore(newForm, addAddressButton)

    totalAddressForms.setAttribute('value', `${addressFormNum+1}`)
}
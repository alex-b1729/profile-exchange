let currentEmail = document.querySelector('#current-email')
let editEmailForm = document.querySelector('#edit-email-form')
let editButton = document.querySelector('#edit-email-button')

editButton.addEventListener('click', toggleEdit)

function toggleEdit(e) {
    currentEmail.hidden = (currentEmail.hidden + 1) % 2
    editEmailForm.hidden = (editEmailForm.hidden + 1) % 2
}
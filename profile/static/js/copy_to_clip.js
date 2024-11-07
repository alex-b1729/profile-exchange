function copyTextToClipboard(elementid) {
    var textToCopy = document.getElementById(elementid).innerText;
    navigator.clipboard.writeText(textToCopy).then(function() {
        console.log('Text copied to clipboard');
    }).catch(function(err) {
        console.error('Could not copy text: ', err);
    });
}
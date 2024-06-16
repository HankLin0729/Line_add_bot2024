document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('openModalButton').addEventListener('click', function() {
        document.getElementById('addEmployeeModal').style.display = 'block';
    });

    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('addEmployeeModal').style.display = 'none';
    });

    document.getElementById('addEmployeeForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const keyword = document.getElementById('keyword').value;
        const dollors = document.getElementById('dollors').value;

        fetch('/add-keyword', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ keyword, dollors }),
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                window.location.reload();
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });

    function fetchAndDisplayKeywords() {
        fetch('/keywords')
            .then(response => response.json())
            .then(keywords => {
                const container = document.getElementById('keyword-container');
                container.innerHTML = '';
                keywords.forEach(keyword => {
                    const div = document.createElement('div');
                    div.className = 'keyword-item';

                    const keywordDiv = document.createElement('div');
                    keywordDiv.textContent = `關鍵字: ${keyword.keyword}`;
                    keywordDiv.className = 'keyword-content';
                    keywordDiv.addEventListener('click', () => makeEditable(keywordDiv, keyword.id, 'keyword'));
                    div.appendChild(keywordDiv);

                    const dollorsDiv = document.createElement('div');
                    dollorsDiv.textContent = `金額: ${keyword.dollors}`;
                    dollorsDiv.className = 'dollors-content';
                    dollorsDiv.addEventListener('click', () => makeEditable(dollorsDiv, keyword.id, 'dollors'));
                    div.appendChild(dollorsDiv);

                    const deleteButton = document.createElement('span');
                    deleteButton.innerHTML = '🗑️';
                    deleteButton.className = 'delete-keyword';
                    deleteButton.onclick = function() { deleteKeyword(keyword.id); };
                    div.appendChild(deleteButton);

                    container.appendChild(div);
                });

            })
            .catch(error => console.log('Error:', error));
    }

    fetchAndDisplayKeywords();
});


function makeEditable(element, id, field) {
    const input = document.createElement('input');

    if (field === 'dollors') {
        input.type = 'number';
    } else {
        input.type = 'text';
    }
    input.value = element.textContent.replace('關鍵字: ', '').replace(' 金額: ', '');
    element.parentNode.replaceChild(input, element);
    input.focus();
    input.select();

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            saveChanges(input, element, id, field);
        }
    });

    input.onblur = function() {
        saveChanges(input, element, id, field);
    };
}



function saveChanges(input, originalElement, id, field) {
    const newValue = input.value;
    fetch('/edit-keyword', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ id, field, newValue }),
        })
        .then(response => response.json())
        .then(data => {
            console.log(data);
            if (field === 'keyword') {
                originalElement.textContent = `關鍵字: ${newValue}`;
            } else if (field === 'dollors') {
                originalElement.textContent = `金額: ${newValue}`;
            }
            input.parentNode.replaceChild(originalElement, input);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}


function deleteKeyword(id) {
    if (confirm('確定要刪除嗎？')) {
        fetch('/delete-keyword', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id }),
            })
            .then(response => response.json())
            .then(data => {
                console.log(data);
                alert('刪除成功');
                window.location.reload();
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    }
}
document.addEventListener('DOMContentLoaded', function() {
    fetchMaterials();
    setInterval(fetchMaterials, 20000);

    document.getElementById('addEmployeeForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const notify = document.getElementById('notify').value;
        const name = document.getElementById('name').value;

        fetch('/add-employee', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notify: notify, name_line: name }),
            })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                document.getElementById('addEmployeeModal').style.display = 'none';
                fetchMaterials();
            })
            .catch(error => console.error('Error:', error));
    });

    document.getElementById('openModalButton').addEventListener('click', function() {
        document.getElementById('addEmployeeModal').style.display = 'block';
    });

    document.querySelector('.close').addEventListener('click', function() {
        document.getElementById('addEmployeeModal').style.display = 'none';
    });
});

function fetchMaterials() {
    fetch('/materials')
        .then(response => response.json())
        .then(data => {
            const materialsContainer = document.querySelector('#materials-container');
            materialsContainer.innerHTML = '';
            data.forEach(material => {
                const materialElement = document.createElement('div');
                materialElement.classList.add('material-container');

                const nameSpan = createEditableSpan(`名稱: ${material.name_line}　　`, 'name', material.id);
                const notifySpan = createEditableSpan(`　　Notify: ${material.notify}`, 'notify', material.id);
                const lineKey = document.createElement('h3');
                lineKey.innerHTML = `key: ${material.key}`, 'key', material.id;


                const editSpan = document.createElement('span');
                editSpan.innerHTML = '';
                editSpan.classList.add('material-edit');
                editSpan.onclick = function() {};

                const deleteSpan = document.createElement('span');
                deleteSpan.innerHTML = '🗑️';
                deleteSpan.classList.add('material-delete');
                deleteSpan.onclick = () => deleteMaterial(material.id);

                materialElement.appendChild(nameSpan);
                materialElement.appendChild(lineKey);
                materialElement.appendChild(notifySpan);
                materialElement.appendChild(editSpan);
                materialElement.appendChild(deleteSpan);
                materialsContainer.appendChild(materialElement);
            });
        })
        .catch(error => console.error('Error:', error));
}


function createEditableSpan(text, type, materialId) {
    const span = document.createElement('span');
    span.textContent = text;
    span.classList.add('material-text');
    span.onclick = function() {
        const originalValue = span.textContent.replace(type === 'name' ? '名稱: ' : 'Notify: ', '');
        const input = document.createElement('input');
        input.type = 'text';
        input.value = originalValue;
        span.parentNode.replaceChild(input, span);
        input.focus();

        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const newValue = input.value;
                if (newValue !== originalValue) {
                    editMaterial(materialId, newValue, type);
                } else {
                    span.textContent = `${type === 'name' ? '名稱: ' : 'Notify: '} ${originalValue}`;
                }
                input.parentNode.replaceChild(span, input);
            }
        });

        input.onblur = function() {

            span.textContent = `${type === 'name' ? '名稱: ' : 'Notify: '} ${input.value}`;
            input.parentNode.replaceChild(span, input);
        };
    };
    return span;
}


function editMaterial(materialId, newValue, type) {
    const updateData = {
        id: materialId,
        new_value: newValue,
        field: type === 'name' ? 'name_line' : 'notify'
    };

    fetch('/edit-material', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(updateData),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Edit successful:', data);
            fetchMaterials();
        })
        .catch(error => console.error('Error:', error));
}


function deleteMaterial(materialId) {
    if (confirm('確定要刪除嗎？')) {
        fetch('/delete-material', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: materialId }),
            })
            .then(response => response.json())
            .then(data => {
                console.log(data.message);
                alert('刪除成功');
                fetchMaterials();
            })
            .catch(error => console.error('Error:', error));
    }
}
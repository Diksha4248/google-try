const form = document.querySelector('form');

form.addEventListener('submit', (e) => {
  e.preventDefault();
  const formData = new FormData(form);
  const userData = Object.fromEntries(formData.entries());

  fetch('/register', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(userData)
  })
  .then(response => response.json())
  .then(data => {
    alert(data.message);
    form.reset();
  })
  .catch(error => {
    console.error(error);
    alert('Error registering user');
  });
});

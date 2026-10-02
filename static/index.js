const form = document.getElementById('post-form');
const postList = document.getElementById('post-list');

form.addEventListener('submit', async function(event) {
  event.preventDefault();

  const formData = new FormData(form);

  const response = await fetch("/api/posts", {
    method: "POST",
    body: formData
  });

  const data = await response.json();
  console.log(data);

  const post = document.createElement('div');

  post.innerHTML = `
    <p>${data.content}</p>
    <img src="${data.image_url}">
    <hr>
  `;

  postList.prepend(post);
    form.reset();
});

async function loadPosts() {
  const response = await fetch("/api/posts");
  const data = await response.json();

  data.data.forEach(function(item) {
    const post = document.createElement('div');

    post.innerHTML = `
      <p>${item.content}</p>
      <img src="${item.image_url}">
      <hr>
    `;

    postList.appendChild(post);
  });
}

loadPosts();
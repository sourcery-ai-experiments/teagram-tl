//                            ██╗████████╗███████╗██╗░░░░░░█████╗░██╗░░░██╗███████╗
//                            ██║╚══██╔══╝╚════██║██║░░░░░██╔══██╗╚██╗░██╔╝╚════██║
//                            ██║░░░██║░░░░░███╔═╝██║░░░░░███████║░╚████╔╝░░░███╔═╝
//                            ██║░░░██║░░░██╔══╝░░██║░░░░░██╔══██║░░╚██╔╝░░██╔══╝░░
//                            ██║░░░██║░░░███████╗███████╗██║░░██║░░░██║░░░███████╗
//                            ╚═╝░░░╚═╝░░░╚══════╝╚══════╝╚═╝░░╚═╝░░░╚═╝░░░╚══════╝
//                                            https://t.me/itzlayz
//
//                                    🔒 Licensed under the СС-by-NC
//                                 https://creativecommons.org/licenses/by-nc/4.0/

function showNotification(title, text) {
  let notificationContainer = document.getElementById("notification-container");

  let notification = document.createElement("div");
  notification.className = "notification";

  let notificationTitle = document.createElement("h3");
  notificationTitle.textContent = title;

  let notificationText = document.createElement("p");
  notificationText.textContent = text;

  notification.appendChild(notificationTitle);
  notification.appendChild(notificationText);

  notificationContainer.appendChild(notification);

  setTimeout(function () {
    notification.classList.add("show");
  }, 100);

  setTimeout(function () {
    notification.classList.remove("show");
    setTimeout(function () {
      notificationContainer.removeChild(notification);
    }, 300);
  }, 3000);
};

function showNotificationError(title, text) {
  let notificationContainer = document.getElementById("notification-container-err");

  let notification = document.createElement("div");
  notification.className = "notification-err";

  let notificationTitle = document.createElement("h3");
  notificationTitle.textContent = title;

  let notificationText = document.createElement("p");
  notificationText.textContent = text;

  notification.appendChild(notificationTitle);
  notification.appendChild(notificationText);

  notificationContainer.appendChild(notification);

  setTimeout(function () {
    notification.classList.add("show");
  }, 100);

  setTimeout(function () {
    notification.classList.remove("show");
    setTimeout(function () {
      notificationContainer.removeChild(notification);
    }, 300);
  }, 3000);
};

let tries = 0;
let __qr = true;
let _interval = null;

let _2fa = false;

function genqr() {
  let port = "";
  if (window.location.port) {
    port = `:${window.location.port}`
  }

  fetch(`${window.location.href}qrcode`, { method: "GET" })
    .then(
      (response) => { return response.text() }
    ).then(
      (data) => {
        let _qr = document.getElementById("qr_placeholder");
        let img = _qr.getElementsByTagName("canvas")[0]


        if (img) {
          img.remove()
        }

        const qrCode = new QRCodeStyling({
          "width": 350,
          "height": 350,
          "data": data,
          "margin": 5,
          "imageOptions": {
            "hideBackgroundDots": true,
            "imageSize": 0.4,
            "margin": 0
          },
          "dotsOptions": {
            "type": "extra-rounded",
            "color": "#000000",
            "gradient": null
          },
          "image": "https://avatars.githubusercontent.com/u/6113871"
        });

        qrCode.append(_qr)
        _qr.title = "";
      }
    )
}

function updating_qr() {
  tries += 1

  if (__qr) {
    fetch(`${window.location.href}checkqr`, { method: "GET" })
      .then(
        (response) => { return response.text() }
      ).then(
        (data) => {
          if (data == 'password') {
            __qr = false
            _2fa = true
            showNotification("2FA", 'Enter 2FA password')

            document.getElementById(
              "qr_placeholder"
            ).remove()
          }
        }
      ).catch(
        (error) => { showNotificationError("ERROR", error); clearInterval(_interval) }
      )
    if (__qr && (tries == 10)) {
      tries = 0

      genqr()
    }
  } else {
    clearInterval(_interval)
  }
}

async function post(endpoint, headers) {
  try {
    const response = await fetch(window.location.href + endpoint, {
      method: 'POST',
      headers: headers,
    });

    return await response.text();
  } catch (error) {
    showNotificationError("Error", error)
  }
}

document.getElementById("enter").onclick = async () => {
  if (!_2fa) {
    const headers = new Headers()

    const _id = document.getElementById("api_id").value
    const _hash = document.getElementById("api_hash").value

    if (!_id || !_hash) {
      showNotificationError("Error", "You didn't enter api_id or api_hash")
      return
    }

    headers.append('id', _id)
    headers.append('hash', _hash)

    try {
      const data = await post('tokens', headers);
      console.log("data is ", data)

      if (!data || data == null) {
        showNotification('Success', 'You are successfully logged, wait for inline bot!');
      } else if (data == 'dialog') {
        showNotification('Choose', 'Login by QRCode or phone number');
        document.getElementById("show-modal").style = "";
        document.getElementById("show-phone").style = "";
      } else {
        console.log(data)
      }
    } catch (error) {
      console.error('Error:', error);
    }
  } else {
    if (__qr) {
      showNotificationError("Error", "You didn't scan QRCode")
      return;
    }

    const headers = new Headers()
    const passwd = document.getElementById("password").value

    if (!passwd) {
      showNotificationError("Error", "You didn't enter 2FA password")
      return
    }

    headers.append("2fa", passwd)

    try {
      const data = await post('twofa', headers)

      if (!data || data == null || data == "null") {
        showNotification('Success', 'You are successfully logged, wait for inline bot!');
      } else {
        console.log(data)
      }
    } catch (error) {
      console.log(data)
    }
  }
}

// im tired to refactor this shit so i'll make some trash
// someone please refactor code above :(
let phone_request_status = false;
async function post_body(endpoint, body) {
  try {
    const response = await fetch(window.location.href + endpoint, {
      method: 'POST',
      body: body
    });

    return await response.text();
  } catch (error) {
    showNotificationError("Error", error)
  }
}

async function send_phone() {
  // post_pody -> next steps 
  // enter valid phone or phone code

  // shutdown -> notification
  let phone = document.getElementById("phone_number");
  if (!phone.value) {
    showNotificationError("Error", "Enter phone number")
    return
  }

  let body = {
    "phone": phone.value
  }

  const response = await post_body("phone_request", JSON.stringify(body));
  showNotification("Enter code", "Enter code from telegram")
}

async function send_code() {
  // post_pody -> next steps 
  // enter valid phone or phone code

  // shutdown -> notification
  if (!phone_request_status) {
    showNotificationError("Error", "You must enter phone")
    return;
  }

  let phone = document.getElementById("phone_code");
  if (!phone.value) {
    showNotificationError("Error", "Enter code")
    return
  }

  let body = {
    "code": phone.value,
  }

  let twofa = document.getElementById("password")
  if (twofa.value) {
    body["twofa"] = twofa.value;
  }

  const response = await post_body("enter_code", JSON.stringify(body));
  switch (response) {
    case "invalid_twofa":
      showNotificationError("Error", "Enter valid 2fa password")
      return;
    case "no_twofa":
      showNotificationError("Error", "Enter 2fa password")
      return;
    case "invalid_phone_code":
      showNotificationError("Error", "Enter valid code")
      return;
    default:
      showNotification("Success", "Wait for inline bot's message")
  }
}

function delete_buttons() {
  document.getElementById("show-modal").remove();
  document.getElementById("show-phone").remove();
}

document.getElementById("show-modal").onclick = async () => {
  delete_buttons();

  let qr_dialog = document.createElement("div");
  qr_dialog.id = "qr_placeholder";

  let container = document.querySelector(".container");
  container.appendChild(qr_dialog);

  if (!_interval) {
    genqr();
    setInterval(updating_qr, 1000)
  }
}

document.getElementById("show-phone").onclick = async () => {
  document.getElementById("enter").remove();
  delete_buttons();

  let label = document.createElement("label");
  label.innerHTML = "Phone number:";

  let input_phone = document.createElement("input");
  input_phone.id = "phone_number";
  input_phone.type = "text";

  let code_label = document.createElement("label");
  code_label.innerHTML = "Phone code:";

  let input_code = document.createElement("input");
  input_code.id = "phone_code";
  input_code.type = "text";

  let container = document.querySelector(".container");

  let submit = document.createElement("input");
  submit.type = "submit";
  submit.id = "enter_phone";
  submit.value = "Enter phone"

  let submit_code = document.createElement("input");
  submit_code.type = "submit";
  submit_code.id = "enter_code";
  submit_code.value = "Enter phone code"

  submit.onclick = send_phone;
  submit_code.onclick = send_code;

  container.appendChild(label);
  container.appendChild(input_phone);

  container.appendChild(code_label);
  container.appendChild(input_code);

  container.appendChild(submit);
  container.appendChild(submit_code);
}

function toggle_theme() {
  document.body.classList.toggle("dark-theme")

  let container = document.querySelector(".container")
  container.classList.toggle("dark-theme")
}

let themeToggle = document.getElementById("theme-toggle")
themeToggle.addEventListener("click", toggle_theme);

document.body.onload = () => { toggle_theme() }
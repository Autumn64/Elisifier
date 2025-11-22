// URL del backend de la instancia al que se conectará con el socket.
const url = "URL";
const socket = io(url);

const setInfo = (message) =>{
    $("#infoMsg").text(message);
}

// Establece el tipo de mensaje a mostrar, su contenido, y su visibilidad.
const setMsg = (type, message, visible) =>{
    if (!["error", "success"].includes(type)) 
        throw new Error(`"type" parameter only accepts values "error" and "success"`);
    selector = {
        "error": "#errorMsg",
        "success": "#successMsg",
    }[type];

    $(selector).text(message);

    if (visible) $(selector).fadeIn("slow");
    else $(selector).fadeOut("slow");
}

socket.on("error", msg =>{
    setMsg("error", msg.message, true);
});

socket.on("output", msg =>{
    $("#outputDiv").append(`${msg.message}<br>`);
    $("#outputDiv").scrollTop($("#outputDiv")[0].scrollHeight);
});

socket.on("status", data =>{
    setInfo(data.message);
});

socket.on("progress", data => {
    $("#progressBar").css("width", `${data.percentage}%`);
    $("#progressBar").text(`${data.percentage}%`);
});

socket.on("success", data =>{
    $("#progressSection").fadeOut("slow");
    $("#downloadSection").fadeIn("slow");

    $("#successMsg").text(data.message);
    $("#downloadBtn").attr("href", `${url}${data.link}`);
    $("#successMsg").fadeIn("slow");
});

socket.on("fatal_error", msg =>{
    $("main section").fadeOut("slow");
    setMsg("error", msg.message, true);
    $("#mainForm").fadeIn("slow"); 
})

$("#mainForm").on("submit", e =>{
    e.preventDefault();
    setMsg("error", "", false);

    if ($("#urls").val().trim() === ""){
        $("#urls").val("");
        setMsg("error", "Debes introducir al menos una URL", true);
        return;
    }

    socket.emit("download", {data: {
        "urls": $("#urls").val(),
        "fmt": $("#fmtSelect").val()
    }});

    $("#mainForm").fadeOut("slow");
    $("#progressSection").fadeIn("slow");
    $("#outputDiv").html("");
    $("#progressBar").css("width", `0`);
    $("#progressBar").text(`0%`);
    setInfo("Descargando...");

    window.scrollTo(0, document.body.scrollHeight);
});

$(window).on("load", () =>{
    if (!localStorage.getItem("elisifier-firstrun")){
        $("#helpModal").modal("show");
        localStorage.setItem("elisifier-firstrun", true);
    }
});
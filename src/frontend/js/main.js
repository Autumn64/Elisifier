const setTheme = (theme, auto) =>{
    const iconTheme = auto ? "auto" : theme;
    $("svg").css("fill", "");
    $("html").attr("data-bs-theme", theme);
    $("#themeDropdown").html($(`#${iconTheme}Icon`).prop("outerHTML"));

    if (theme !== "dark") return;

    $("svg").css("fill", "white");
}

const detectScheme = () =>{
    const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

	if (prefersDark) {
        setTheme("dark", true);
    };
}

$(".theme-btn").on("click", function(){
    const currTheme = $(this).attr("theme-toggle");

    if (currTheme === "auto"){
        localStorage.removeItem("elisifier-theme");
        detectScheme();
        return;
    }

    localStorage.setItem("elisifier-theme", currTheme);
    setTheme(currTheme, false);
});

$(() =>{
    const savedTheme = localStorage.getItem("elisifier-theme");

    if ([null, undefined, "", "auto"].includes(savedTheme)){
        detectScheme();
        return;
    }

    setTheme(savedTheme, false);
});
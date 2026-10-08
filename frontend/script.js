const boton1 = document.getElementById("boton1");
const resultado1 = document.getElementById("resultado1");

boton1.addEventListener("click", async () => {
    resultado1.textContent = "Conectando con el backend...";

    try {
        const respuesta1 = await fetch("http://localhost:9000/");
        const datos1 = await respuesta1.json();

        resultado1.textContent = datos1.mensaje;
    } catch (error) {
        resultado1.textContent = "No se pudo conectar con el backend.";
        console.error(error);
    }
});

const boton2 = document.getElementById("boton2");
const resultado2 = document.getElementById("resultado2");

boton2.addEventListener("click", async () => {
    resultado2.textContent = "Conectando con el backend...";

    try {
        const respuesta2 = await fetch("http://localhost:9000/");
        const datos2 = await respuesta2.json();
        resultado2.textContent = datos2.mensaje;
    } catch (error) {
        resultado2.textContent = "No se pudo conectar con el backend.";
        console.error(error);
    }
});
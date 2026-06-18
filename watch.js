import chokidar from 'chokidar';
import { exec } from 'child_process';
import { fileURLToPath } from 'url';
import path from 'path';

// Usar import.meta.url para obtener el directorio de ejecución
const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Ruta de la carpeta que deseas observar (por ejemplo, 'src/')
const directoryToWatch = path.join(__dirname, 'src');

// Ruta de la carpeta de destino después del build
const destinationFolder = path.join(__dirname, 'static', 'dist');

// Verificar si estamos en un sistema operativo Windows o Unix-like
const isWindows = process.platform === 'win32';

// Iniciar el observador
const watcher = chokidar.watch(directoryToWatch, {
  ignored: '*.git',
  ignored: /node_modules|dist|build/, // Opcional: Ignorar cambios en node_modules
  awaitWriteFinish: {
    stabilityThreshold: 2000,
    pollInterval: 100
  },
  persistent: true,        // Mantener el observador en ejecución
  ignoreInitial: true,     // Ignorar el primer evento cuando se inicia el observador
});

// Escuchar eventos de cambios
watcher
  .on('change', (filePath) => {
    console.log(`Archivo modificado: ${filePath}`);
    // Ejecutar el comando npm run build cuando un archivo cambie
    exec('npm run build', (err, stdout, stderr) => {
      if (err) {
        console.error(`Error al ejecutar el build: ${err}`);
        return;
      }
      console.log(stdout);
      console.error(stderr);

      // Usar comillas para las rutas con espacios
      const rmCommand = isWindows
        ? `for %f in (build\\*) do move "%f" "${destinationFolder}\\"`  // Usar un bucle para mover los archivos
        : `mv build/* ${destinationFolder}`;  // Comando de Linux/Unix

      exec(rmCommand, (rmErr, rmStdout, rmStderr) => {
        if (rmErr) {
          console.error(`Error al limpiar el directorio de destino: ${rmErr}`);
          return;
        }
        console.log(`Directorio de destino limpiado: ${destinationFolder}`);
        console.log(rmStdout);
        console.error(rmStderr);

        // Mover los archivos después del build
        const mvCommand = isWindows
          ? `move build\\* ${destinationFolder}\\`  // Comando de Windows
          : `mv build/* ${destinationFolder}`;  // Comando de Linux/Unix

        exec(mvCommand, (mvErr, mvStdout, mvStderr) => {
          if (mvErr) {
            console.error(`Error al mover archivos: ${mvErr}`);
            return;
          }
          console.log(`Archivos movidos a ${destinationFolder}`);
          console.log(mvStdout);
          console.error(mvStderr);
        });
      });
    });
  })
  .on('add', (filePath) => {
    console.log(`Archivo añadido: ${filePath}`);
  })
  .on('unlink', (filePath) => {
    console.log(`Archivo eliminado: ${filePath}`);
  })
  .on('error', (error) => {
    console.error(`Error en la observación: ${error}`);
  });

console.log(`Observando cambios en la carpeta: ${directoryToWatch}`);

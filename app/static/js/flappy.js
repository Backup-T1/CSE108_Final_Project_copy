console.log("Flappy loads")

document.addEventListener("DOMContentLoaded", () =>{

    console.log("DOM ready")    

    const canvas = document.getElementById("flappy-canvas");
    if (!canvas){
        return;
    }
    const ctx = canvas.getContext("2d") 

    const bg_color = "rgb(167, 199, 231)";
    const bird_color = "rgb(255, 245, 165)";
    const pipe_color = "rgb(178, 226, 177)";    

    let bird = {x: 100, y: 200, w: 30, h: 30, speed: 0};  

    let pipes = []
    let score = 0;  

    let gameStart = false;
    let gameOver = false;

    function resetGame(){
        bird.x = 100;
        bird.y = 200;
        bird.speed = 0;
        pipes = [];
        score = 0;

    }   

    

    canvas.addEventListener("click", () => {
        
        if (!gameStart || gameOver){
            resetGame();
            gameStart = true;
            gameOver = false;
            bird.speed = -5;
            return;
        }
        bird.speed = -5;
    }); 

    function spawnPipe(){
        const gapY = Math.floor(Math.random() * (300 - 100)) + 100;
        const pipeWidth = 50;
        const pipeGap = 150;    

        const topHeight = gapY - pipeGap / 2;
        const bottomY = gapY +pipeGap / 2;
        const bottomHeight = 400 - bottomY;  
        

        pipes.push({x: 400, y: 0, w: pipeWidth, h: topHeight});
        pipes.push({x: 400, y: bottomY, w: pipeWidth, h: bottomHeight});
    }   

    function update(){

        if (!gameStart || gameOver){
            return;
        }

        bird.speed += 0.3;
        bird.y += bird.speed;   

        if (pipes.length === 0 || pipes[pipes.length - 1].x < 250){
            spawnPipe();
        }   

        pipes.forEach((pipe, i) =>{
            pipe.x -= 2; 

            if (pipe.x + pipe.w < 0){
                pipes.splice(i, 1);
            }
            if (pipe.x + pipe.w === bird.x){
                pipe.scored = true;
                score++;
            }
            if (bird.x < pipe.x + pipe.w && bird.x + bird.w > pipe.x && bird.y < pipe.y + pipe.h && bird.y + bird.h > pipe.y){
                if (!gameOver){ 
                    gameOver = true;
                    submitScore();
                }
            }
        });
        if (bird.y < 0 || bird.y +bird.h > 400){
            if (!gameOver){ 
                gameOver = true;
                submitScore();
            }
            
        }
    }   

    function draw(){
        ctx.fillStyle = bg_color;
        ctx.fillRect(0, 0, 400, 400);   

        ctx.fillStyle = bird_color;
        ctx.fillRect(bird.x, bird.y, bird.w, bird.h);   

        ctx.fillStyle = pipe_color;
        pipes.forEach( pipe =>{
            ctx.fillRect(pipe.x, pipe.y, pipe.w, pipe.h);
        });

        ctx.fillStyle = "rgb(85, 85, 85)";
        ctx.font = "30px arial";
        ctx.fillText("Score: " + score, 20, 40);

        if (!gameStart){
            ctx.fillStyle = "rgb(25, 25, 75)";
            ctx.fillRect(0, 0, 400, 400);

            ctx.fillStyle = "white";
            ctx.textAlign = "center";

            ctx.font = "48px Press Start 2P";
            ctx.fillText("Flappy Pet", 200, 145);

            ctx.font = "28px Press Start 2P";
            ctx.fillText("CLICK to play", 200, 200);

            ctx.textAlign = "left";
        }

        if (gameOver){
            ctx.fillStyle = "rgb(25, 25, 75)";
            ctx.fillRect(0, 0, 400, 400);

            ctx.fillStyle = "white";
            ctx.textAlign = "center";

            ctx.font = "48px Press Start 2P";
            ctx.fillText("Game over", 200, 145);

            ctx.font = "38px Press Start 2P";
            ctx.fillText("Score: " + score, 200, 195);

            ctx.font = "28px Press Start 2P";
            ctx.fillText("CLICK to play", 200, 245);

            ctx.textAlign = "left";
        }
    }   

    function loop(){
        update();
        draw();
        requestAnimationFrame(loop);
    }   

    async function submitScore() {
        try{
            const res = await fetch("/shop/flappy/play",{
                method:"POST", 
                headers:{
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ score })
            });

            const data = await res.json();

            if (data.ok){
                const coinPill = document.querySelector(".coin-pill");

                if (coinPill){
                    coinPill.textContent = `${data.coins} Coins`;
                }

                console.log(`+${data.payout} Coins`);
            }
        }catch(err){
            console.log("Error, please try again", err);
        }
    }

    resetGame();
    gameStart = false;
    gameOver = false;
    loop();
});
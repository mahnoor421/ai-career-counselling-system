document.addEventListener("DOMContentLoaded", function () {


    const suggestionBox = document.getElementById("suggestions");


    if (!suggestionBox) {
        return;
    }



    let step = suggestionBox.dataset.step;



    let suggestions = [];



    if(step == 1){

        suggestions = [

            "Matric",
            "ICS",
            "FSc Pre-Medical",
            "FSc Pre-Engineering",
            "I.Com",
            "BSCS",
            "BBA",
            "MBBS",
            "LLB"

        ];

    }





    else if(step == 2){


        suggestions = [

            "Artificial Intelligence",
            "Medicine",
            "Engineering",
            "Business",
            "Law",
            "Psychology",
            "Graphic Design",
            "Agriculture"

        ];


    }





    else if(step == 3){


        suggestions = [

            "Programming",
            "Communication",
            "Leadership",
            "Research",
            "Creativity",
            "Management"

        ];


    }





    else if(step == 4){


        suggestions = [

            "High Salary",
            "Research",
            "Government Job",
            "Remote Work",
            "Business"

        ];


    }





    suggestions.forEach(function(item){



        let button = document.createElement("button");


        button.innerText = item;


        button.className = "suggestion-btn";



        button.onclick = function(){


            sendSuggestion(item);


        };



        suggestionBox.appendChild(button);



    });



});






function sendSuggestion(text){


    let input = document.querySelector(
        'input[name="message"]'
    );


    input.value = text;


    input.form.submit();


}
window.onload = function(){

    let messages = document.getElementById("messages");

    if(messages){

        messages.scrollTop = messages.scrollHeight;

    }

};
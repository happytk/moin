function toggleMenu (objID)
{
    if (document.getElementById (objID).style.display != "block")
   {
        document.getElementById (objID).style.display = "block";
        document.getElementById ('togglelink').innerHTML = "[ fewer options ]";
    }
    else
    {
        document.getElementById (objID).style.display = "none";
        document.getElementById ('togglelink').innerHTML = "[ more options ]";
     }
}

function toggleMenuWithTitle (obj, title_open, title_close, objID)
{
    if (document.getElementById (objID).style.display != "block")
   {
        document.getElementById (objID).style.display = "block";
        //document.getElementById ('togglelink').innerHTML = title_open;
        obj.innerHTML = title_open;
    }
    else
    {
        document.getElementById (objID).style.display = "none";
        //document.getElementById ('togglelink').innerHTML = title_close;
        obj.innerHTML = title_close;
     }
}
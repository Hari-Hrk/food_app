let autocomplete;

function initAutoComplete(){
autocomplete = new google.maps.places.Autocomplete(
    document.getElementById('id_address'),
    {
        types: ['geocode', 'establishment'],
        //default in this app is "IN" - add your country code
        componentRestrictions: {'country': ['in']},
    })
// function to specify what should happen when the prediction is clicked
autocomplete.addListener('place_changed', onPlaceChanged);
}

function onPlaceChanged (){
    var place = autocomplete.getPlace();

    // User did not select the prediction. Reset the input field or alert()
    if (!place.geometry){
        document.getElementById('id_address').placeholder = "Start typing...";
    }
    else{
        console.log('place name=>', place.name)
    }
    // get the address components and assign them to the fields
}


// document ready start here
$(document).ready(function(){

    // add to cart
    $('.add_to_cart').on('click',function(e){
        e.preventDefault();
        food_id = $(this).attr('data-id')
        url = $(this).attr('data-url')
        
        $.ajax({
            type:'GET',
            url:url,
            success:function(response){
                console.log(response);
                if(response.status == 'login_required'){
                    swal(response.message,'','info').then(function(){
                        window.location='/login'
                    })
                }else if (response.status == 'failed') {
                    swal(response.message,'','error')
                }
                else{
                $('#cart_counter').html(response.cart_counter['cart_count'])
                $('#qty-'+food_id).html(response.qty)

                // subtotal,tax,grand total
                    applyCartAmounts(
                        response.cart_amount['subtotal'],
                        response.cart_amount['tax'],
                        response.cart_amount['grand_total']
                    )
                }
            }
        })
    })
    // place the cart item quantity on load
    $('.item_qty').each(function(){
        var the_id = $(this).attr('id')
        var qty = $(this).attr('data-qty')
        $('#'+the_id).html(qty)
    })

    // decrease cart
    $('.decrease_cart').on('click',function(e){
        e.preventDefault();
        food_id = $(this).attr('data-id')
        url = $(this).attr('data-url')
        cart_id = $(this).attr('id')

        $.ajax({
            type:'GET',
            url:url,
            success:function(response){
                console.log(response);
                if(response.status == 'login_required'){
                    swal(response.message,'','info').then(function(){
                        window.location='/login'
                    })
                }else if (response.status == 'failed') {
                    swal(response.message,'','error')
                }
                else{
                $('#cart_counter').html(response.cart_counter['cart_count'])
                $('#qty-'+food_id).html(response.qty)

                applyCartAmounts(
                    response.cart_amount['subtotal'],
                    response.cart_amount['tax'],
                    response.cart_amount['grand_total']
                )

                if (window.location.pathname == '/cart/') {
                removeCartItem(response.qty,cart_id)
                checkEmptyCart()
                }
             }
            }
        })
    })

// delete cart items
$('.delete_cart').on('click',function(e){
    e.preventDefault();
    cart_id = $(this).attr('data-id')
    url = $(this).attr('data-url')
    console.log('cart id =====> ',cart_id);
    $.ajax({
        type:'GET',
        url:url,
        success:function(response){
            console.log(response);
            if(response.status == 'failed'){
                swal(response.message,'','error')
            }
            else{
            $('#cart_counter').html(response.cart_counter['cart_count'])
            swal(response.status,response.message,'success');

            applyCartAmounts(
                response.cart_amount['subtotal'],
                response.cart_amount['tax'],
                response.cart_amount['grand_total']
            )

            removeCartItem(0,cart_id)
            checkEmptyCart();
            }
        }
    })
})

//delete the cart element if the qty is 0
function removeCartItem(cartItemQty,cart_id){
        if (cartItemQty <= 0) {
            document.getElementById('cart-item-'+cart_id).remove()
        }
}

//if cart is empty
function checkEmptyCart(){
    var cart_counter = document.getElementById('cart_counter').innerHTML
    if (cart_counter == 0) {
        document.getElementById('empty-cart').style.display='block'
    }
}
//apply cart amount
function applyCartAmounts(subtotal,tax,grand_total){
    if (window.location.pathname == '/cart/') {
        $('#subtotal').html(subtotal)
        $('#tax').html(tax)
        $('#total').html(grand_total)
      
    }
}

// add hours
// making ajax request for add hours
    $('.add_hour').on('click',function(e){
        e.preventDefault()
        var day = document.getElementById('id_day').value
        var from_hour = document.getElementById('id_from_hour').value
        var to_hour = document.getElementById('id_to_hour').value
        var is_closed = document.getElementById('id_is_closed').checked
        var csrf_token = $('input[name=csrfmiddlewaretoken]').val()//this jquery
        var url = document.getElementById('add_hour_url').value
        

        if (is_closed) {
            is_closed = 'True'
            condition = "day != ''"
        } else {
            is_closed = 'False'
            condition = "from_hour != '' && to_hour != ''"
        }

        if (eval(condition)) {
            $.ajax({
                type : 'POST',
                url : url,
                data :{
                    'day':day,
                    'from_hour':from_hour,
                    'to_hour':to_hour,
                    'is_closed':is_closed,
                    'csrfmiddlewaretoken':csrf_token
                },
                success:function(res){
                    if (res.status == 'success') {
                        if (res.is_closed == 'Closed') {
                            html = `<tr id="hour-${res.id}"><td><b>${res.day}</b></td><td>Closed</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/${res.id}/">Remove</a></td></tr>`
                        } else {
                            html = `<tr id="hour-${res.id}"><td><b>${res.day}</b></td><td>${res.from_hour} - ${res.to_hour}</td><td><a href="#" class="remove_hour" data-url="/vendor/opening-hours/remove/${res.id}/">Remove</a></td></tr>` 
                        }
                        $('.opening_hours').append(html)
                        document.getElementById('opening_hours').reset()
                    }
                    else{
                        swal(res.message,'','error')
                    }
                }
            })
        } else {
            swal('fill all the fields','','info');
        }

    })

// REMOVE HOURS
    $(document).on('click','.remove_hour',function(e){
        e.preventDefault()
        url = $(this).attr('data-url');
        console.log('url is ===> ',url);
        $.ajax({
            type:'GET',
            url:url,
            success:function(res){
                if (res.status == 'success') {
                    document.getElementById('hour-'+res.id).remove()
                }
            }
        })
    })

})
// document ready end here


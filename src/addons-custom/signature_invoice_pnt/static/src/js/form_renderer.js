odoo.define('signature_invoice_pnt.account_move', function(require) {
    "use strict";

    var core = require('web.core');
    var Widget= require('web.Widget');
    var widgetRegistry = require('web.widget_registry');
    var FieldManagerMixin = require('web.FieldManagerMixin');
    var fieldRegistry = require('web.field_registry');
    var dataset = require('web.data');
    var Dialog = require('web.Dialog');
    var ControlPanel = require('web.ControlPanel');
    var Pager = require('web.Pager');
    var rpc = require('web.rpc');
    var QWeb = core.qweb;
    var _t = core._t;
    var imgWidth;
	var imgHeight;

    var MyWidget = Widget.extend({
        template: 'SignatureInvoiceButton',
        events: {
            'click .o_signature_invoice': '_onSignatureInvoice',
        },

        init: function (parent, model, state) {
            this._super(parent);
            this.model = model;
        },

    	start: function(){
            var self = this;
            this._super.apply(this, arguments);
            self.$el.html(QWeb.render('SignatureInvoiceButton', {
                'widget': self,
            }));
            setTimeout(function(){
                self.$el.parent().find('signbutton').focus();
            }, 60);
        },

       _onSignatureInvoice: function () {
//	        debugger;
	        var self = this;
	        var invoice_id_sel = self.model.data.id;
//	        alert('id capçalera: ' + self.model.data.id);
	        if (invoice_id_sel)
	        {
//	            alert(sale_id_sel)
	            var canvasObj = document.getElementById('cnv');
		        canvasObj.getContext('2d').clearRect(0, 0, canvasObj.width, canvasObj.height);
		        imgWidth = canvasObj.width;
		        imgHeight = canvasObj.height;
		        var message = { "firstName": "", "lastName": "", "eMail": "", "location": "", "imageFormat": 1, "imageX": imgWidth, "imageY": imgHeight, "imageTransparency": false, "imageScaling": false, "maxUpScalePercent": 0.0, "rawDataFormat": "ENC", "minSigPoints": 25 };
	            document.addEventListener('SigCaptureWeb_SignResponse',(
                    function (event, invoice_id=invoice_id_sel) {
 	                    var str = event.target.getAttribute("SigCaptureWeb_msgAttri");
       	                var obj = JSON.parse(str);
                        var obj2 = JSON.parse(JSON.stringify(obj));
	                    var ctx = document.getElementById('cnv').getContext('2d');
    			        if (obj2.errorMsg != null && obj2.errorMsg!="" && obj2.errorMsg!="undefined")
			            {
                            alert(obj2.errorMsg);
                        }
                        else
			            {
                            if (obj2.isSigned)
        				    {
                                var id_pos = Number(event.currentTarget.URL.indexOf("id=")) + 3;
                                var current_invoice_id = event.currentTarget.URL.substring(id_pos,(id_pos + 10)).match(/\d+/)[0];
//                                alert('URL_id: ' + current_sale_id)
//                                var sale_orig = event.currentTarget.URL.substring(48,57).match(/\d+/)[0];
                                if (invoice_id == current_invoice_id)
                                {
//                    	            alert('id: ' + sale_id)
                                    rpc.query({
                                    model: 'account.move',
                                    method: 'signature_assign',
                                    args: [{
                                        'invoice_id': invoice_id,
                                        'imagedata': obj2.imageData,
                                        'rawdata': obj2.rawData
                                    }],
                                    }).then(function (booleano) {
//                                          sale_id = null
//                                      if (booleano) {
//                                        alert('Firma guardada correctamente')
//                                    } else {
//                                        alert('Error al guardar la firma')
//                                    }
                                    });
                                }
                            }
                        }
	                }),
		            false);
		        var messageData = JSON.stringify(message);
		        var element = document.createElement("SigCaptureWeb_ExtnDataElem");
		        element.setAttribute("SigCaptureWeb_MsgAttribute", messageData);
		        document.documentElement.appendChild(element);
		        var evt = document.createEvent("Events");
		        evt.initEvent("SigCaptureWeb_SignStartEvent", true, false);
		        element.dispatchEvent(evt);
		     }
		     else
		     {
		        alert('Debe guardar el documento antes de poder firmarlo digitalmente')
		     }
        },

    });

    widgetRegistry.add(
        'widget_pnt_signature_invoice_button', MyWidget
    );

return MyWidget;
});
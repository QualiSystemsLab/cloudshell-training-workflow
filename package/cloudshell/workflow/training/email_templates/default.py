def load_template():
    subject = 'Welcome to Training'

    html_template = '''
<!DOCTYPE html>
<html lang="en">

<div>
    <h2 style="text-align: center;"><span style="color: #F76723;"><strong>Welcome to Training</strong></span></h2>
</div>

<div>
    <p><span style="color: #000000;">Please retain this email as it is how you will access your online lab environment. It also contains your credentials (if needed) and links to helpful materials.</span></p>
</div>

<div>
    <p><span style="color: #000000;">I&rsquo;m looking forward to our class together</span></p>
</div>

<div>
    <p><span style="color: #000000;"><strong>To access your CloudShell Environment please use the following:</strong></span></p>
</div>

<div>
    <span style="color: #000000;"><span style="color: #F76723;"><strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Environment details:</strong></span></span><br>
</div>

<div>
    <span style="color: #000000;">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
        <a href="{sandbox_link}"> Environment Link </a>
    </span>
</div>

</body>
</html>
'''

    return subject, html_template

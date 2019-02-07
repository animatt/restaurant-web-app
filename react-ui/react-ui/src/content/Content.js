import React, {Component} from 'react';
import {Route, Switch} from 'react-router-dom';

import Welcome from './welcome/Welcome';
import SelectRes from './selectres/SelectRes';
import Login from './registration/Login';

class Content extends Component {
	constructor(props) {
		super(props);
	}
	render() {
		return (
			<div className="col-sm-10">
			  <main className="Content">
				<switch>
				  <Route exact path='/' component={Welcome} />
				  <Route exact path='/reservation' component={SelectRes} />
				  <Route exact path='/login' component={Login} />
				</switch>
			  </main>
			</div>
		);
	}
}
export default Content;
